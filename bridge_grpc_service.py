"""
Bridge gRPC Service.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import traceback
import base64
import os

import grpc
import phonenumbers
from phonenumbers import geocoder

import bridge_pb2
import bridge_pb2_grpc

from content_parser import decode_content, extract_content, extract_content_v2
from vault_grpc_client import (
    create_bridge_entity,
    decrypt_payload,
    authenticate_bridge_entity,
)

from utils import get_logger, get_bridge_details_by_shortcode, import_module_dynamically
from notification_dispatcher import dispatch_notifications

logger = get_logger(__name__)


class BridgeService(bridge_pb2_grpc.EntityServiceServicer):
    """Bridge Service Descriptor"""

    def handle_create_grpc_error_response(
        self, context, response, error, status_code, **kwargs
    ):
        """
        Handles the creation of a gRPC error response.

        Args:
            context (grpc.ServicerContext): The gRPC context object.
            response (callable): The gRPC response object.
            error (Exception or str): The exception instance or error message.
            status_code (grpc.StatusCode): The gRPC status code to be set for the response
                (e.g., grpc.StatusCode.INTERNAL).
            user_msg (str, optional): A user-friendly error message to be returned to the client.
                If not provided, the `error` message will be used.
            error_type (str, optional): A string identifying the type of error.
                When set to "UNKNOWN", it triggers the logging of a full exception traceback
                for debugging purposes.
            error_prefix (str, optional): An optional prefix to prepend to the error message
                for additional context (e.g., indicating the specific operation or subsystem
                that caused the error).

        Returns:
            An instance of the specified response with the error set.
        """
        user_msg = kwargs.get("user_msg")
        error_type = kwargs.get("error_type")
        error_prefix = kwargs.get("error_prefix")

        if not user_msg:
            user_msg = str(error)

        if error_type == "UNKNOWN":
            traceback.print_exception(type(error), error, error.__traceback__)

        error_message = f"{error_prefix}: {user_msg}" if error_prefix else user_msg
        context.set_details(error_message)
        context.set_code(status_code)

        return response()

    def handle_request_field_validation(
        self, context, request, response, required_fields
    ):
        """
        Validates the fields in the gRPC request.

        Args:
            context: gRPC context.
            request: gRPC request object.
            response: gRPC response object.
            required_fields (list): List of required fields, can include tuples.

        Returns:
            None or response: None if no missing fields,
                error response otherwise.
        """

        def validate_field(field):
            if not getattr(request, field, None):
                return self.handle_create_grpc_error_response(
                    context,
                    response,
                    f"Missing required field: {field}",
                    grpc.StatusCode.INVALID_ARGUMENT,
                )

            return None

        for field in required_fields:
            validation_error = validate_field(field)
            if validation_error:
                return validation_error

        return None

    def PublishContent(self, request, context):
        """Handles publishing bridge payload"""

        response = bridge_pb2.PublishContentResponse
        logger.debug("Received PublishContent request: %s", request.__dict__)

        def create_entity(
            client_publish_pub_key=None,
            ownership_proof_response=None,
            server_pub_key_identifier=None,
            server_pub_key_version=None,
            language=None,
        ):
            parsed_number = phonenumbers.parse(request.metadata["From"])
            region_code = geocoder.region_code_for_number(parsed_number)

            create_entity_response, create_entity_error = create_bridge_entity(
                phone_number=request.metadata["From"],
                country_code=region_code,
                client_publish_pub_key=client_publish_pub_key,
                ownership_proof_response=ownership_proof_response,
                server_pub_key_identifier=(
                    str(server_pub_key_identifier)
                    if server_pub_key_identifier is not None
                    else None
                ),
                server_pub_key_version=server_pub_key_version,
                language=language,
            )

            if create_entity_error:
                error_message = create_entity_error.details()
                if error_message.startswith("OTP not initiated. "):
                    return response(message=error_message, success=True), None
                return None, self.handle_create_grpc_error_response(
                    context, response, error_message, create_entity_error.code()
                )

            if not create_entity_response.success:
                return None, response(
                    message=create_entity_response.message,
                    success=create_entity_response.success,
                )

            return (
                response(
                    message=create_entity_response.message,
                    success=create_entity_response.success,
                ),
                None,
            )

        def authenticate_entity(language=None):
            authentication_response, authentication_error = authenticate_bridge_entity(
                phone_number=request.metadata["From"], language=language
            )

            if authentication_error:
                return None, self.handle_create_grpc_error_response(
                    context,
                    response,
                    authentication_error.details(),
                    authentication_error.code(),
                )

            if not authentication_response.success:
                return None, response(
                    message=authentication_response.message,
                    success=authentication_response.success,
                )

            return (
                response(
                    message=authentication_response.message,
                    success=authentication_response.success,
                ),
                None,
            )

        def get_bridge_info(bridge_letter):
            bridge_info, bridge_err = get_bridge_details_by_shortcode(bridge_letter)
            if bridge_info is None:
                return None, self.handle_create_grpc_error_response(
                    context,
                    response,
                    bridge_err,
                    grpc.StatusCode.INVALID_ARGUMENT,
                )
            return bridge_info, None

        def decrypt_message(phone_number, encrypted_content):
            decrypt_payload_response, decrypt_payload_error = decrypt_payload(
                phone_number=phone_number,
                payload_ciphertext=base64.b64encode(encrypted_content).decode("utf-8"),
            )
            if decrypt_payload_error:
                return None, self.handle_create_grpc_error_response(
                    context,
                    response,
                    decrypt_payload_error.details(),
                    decrypt_payload_error.code(),
                )
            if not decrypt_payload_response.success:
                return None, response(
                    message=decrypt_payload_response.message,
                    success=decrypt_payload_response.success,
                )
            return decrypt_payload_response, None

        def send_message(platform_name, content_parts, payload_version):
            if platform_name == "email_bridge":
                email_bridge_module = import_module_dynamically(
                    "email_bridge.simplelogin.client",
                    os.path.join("bridges", "email_bridge", "simplelogin", "client.py"),
                    os.path.join("bridges", "email_bridge"),
                )

                content_map = {
                    "v0": lambda c: {
                        "to": c[0],
                        "cc": c[1],
                        "bcc": c[2],
                        "subject": c[3],
                        "body": c[4],
                    },
                    "v1": lambda c: {
                        "to": c[0],
                        "cc": c[1],
                        "bcc": c[2],
                        "subject": c[3],
                        "body": c[4],
                    },
                    "v2": lambda c: c,
                }
                content = content_map[payload_version](content_parts)
                email_send_success, email_send_message = email_bridge_module.send_email(
                    phone_number=request.metadata["From"],
                    to_email=content["to"],
                    cc_email=content["cc"],
                    bcc_email=content["bcc"],
                    subject=content["subject"],
                    body=content["body"],
                    image=content.get("image"),
                )
                if not email_send_success:
                    return None, self.handle_create_grpc_error_response(
                        context,
                        response,
                        email_send_message,
                        grpc.StatusCode.INVALID_ARGUMENT,
                    )

                return email_send_message, None

            return None, self.handle_create_grpc_error_response(
                context,
                response,
                f"Sorry, the platform '{platform_name}' is not supported.",
                grpc.StatusCode.UNIMPLEMENTED,
            )

        def handle_publication_notifications(
            platform_name, status="failed", country_code=None
        ):
            notifications = [
                {
                    "notification_type": "event",
                    "target": "publication",
                    "details": {
                        "platform_name": platform_name,
                        "source": "bridges",
                        "status": status,
                        "country_code": country_code,
                    },
                },
            ]
            dispatch_notifications(notifications)

        try:
            invalid_fields_response = self.handle_request_field_validation(
                context, request, response, ["content"]
            )
            if invalid_fields_response:
                return invalid_fields_response

            decoded_result, decode_error = decode_content(content=request.content)
            if decode_error:
                return self.handle_create_grpc_error_response(
                    context,
                    response,
                    decode_error,
                    grpc.StatusCode.INVALID_ARGUMENT,
                    error_prefix="Error Decoding Content",
                    error_type="UNKNOWN",
                )
            if public_key := decoded_result.get("public_key"):
                create_response, create_error = create_entity(
                    client_publish_pub_key=base64.b64encode(public_key).decode("utf-8"),
                    server_pub_key_identifier=decoded_result.get("skid"),
                    language=decoded_result.get("language"),
                )
                if create_error:
                    return create_error
                if "skid" not in decoded_result:
                    return create_response

            bridge_info = None
            if bridge_letter := decoded_result.get("bridge_letter"):
                bridge_info, bridge_info_error = get_bridge_info(bridge_letter)
                if bridge_info_error:
                    return bridge_info_error

            if auth_code := decoded_result.get("auth_code"):
                create_response, create_error = create_entity(
                    ownership_proof_response=auth_code
                )
                if create_error:
                    return create_error
                if "content_ciphertext" not in decoded_result:
                    return response(success=True, message=create_response.message)

            if (
                "skid" not in decoded_result
                and "auth_code" not in decoded_result
                and "public_key" not in decoded_result
            ):
                _, authenticate_error = authenticate_entity(
                    language=decoded_result.get("language")
                )
                if authenticate_error:
                    return authenticate_error

            decrypt_response, decrypt_error = decrypt_message(
                phone_number=request.metadata["From"],
                encrypted_content=decoded_result["content_ciphertext"],
            )
            if decrypt_error:
                return decrypt_error

            payload_version = decoded_result.get("version", "v0")
            logger.debug("Request metadata: %s", request.metadata)
            logger.debug("image_length: %s", request.metadata.get("Image-Length"))
            content_extraction_map = {
                "v0": lambda d: extract_content(
                    bridge_name=bridge_info["name"],
                    content=base64.b64decode(d).decode("utf-8"),
                ),
                "v1": lambda d: extract_content(
                    bridge_name=bridge_info["name"],
                    content=base64.b64decode(d).decode("utf-8"),
                ),
                "v2": lambda d: extract_content_v2(
                    bridge_name=bridge_info["name"],
                    content=base64.b64decode(d),
                    image_length=(
                        0
                        if not request.metadata.get("Image-Length")
                        else int(request.metadata.get("Image-Length"))
                    ),
                ),
            }

            extracted_content, extraction_error = content_extraction_map[
                payload_version
            ](decrypt_response.payload_plaintext)
            if extraction_error:
                return self.handle_create_grpc_error_response(
                    context,
                    response,
                    extraction_error,
                    grpc.StatusCode.INVALID_ARGUMENT,
                )

            _, message_error = send_message(
                bridge_info["name"], extracted_content, payload_version
            )

            if message_error:
                handle_publication_notifications(
                    bridge_info["name"],
                    status="failed",
                    country_code=decrypt_response.country_code,
                )
                return message_error

            handle_publication_notifications(
                bridge_info["name"],
                status="published",
                country_code=decrypt_response.country_code,
            )
            return response(
                success=True,
                message=f"Successfully published {bridge_info['name']} message",
            )

        except Exception as exc:
            handle_publication_notifications(
                bridge_info["name"],
                status="failed",
                country_code=decrypt_response.country_code,
            )
            return self.handle_create_grpc_error_response(
                context,
                response,
                exc,
                grpc.StatusCode.INTERNAL,
                user_msg="Oops! Something went wrong. Please try again later.",
                error_type="UNKNOWN",
            )
