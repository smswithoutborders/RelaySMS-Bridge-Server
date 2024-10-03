"""
Bridge gRPC Service.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import grpc

import bridge_pb2
import bridge_pb2_grpc

from utils import get_logger

logger = get_logger(__name__)


class BridgeService(bridge_pb2_grpc.EntityServiceServicer):
    """Bridge Service Descriptor"""

    def handle_create_grpc_error_response(
        self, context, response, sys_msg, status_code, **kwargs
    ):
        """
        Handles the creation of a gRPC error response.

        Args:
            context: gRPC context.
            response: gRPC response object.
            sys_msg (str or tuple): System message.
            status_code: gRPC status code.
            user_msg (str or tuple): User-friendly message.
            error_type (str): Type of error.

        Returns:
            An instance of the specified response with the error set.
        """
        user_msg = kwargs.get("user_msg")
        error_type = kwargs.get("error_type")

        if not user_msg:
            user_msg = sys_msg

        if error_type == "UNKNOWN":
            logger.exception(sys_msg)

        context.set_details(user_msg)
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

        def validate_fields():
            return self.handle_request_field_validation(
                context, request, response, ["content"]
            )

        try:
            invalid_fields_response = validate_fields()
            if invalid_fields_response:
                return invalid_fields_response

        except Exception as exc:
            return self.handle_create_grpc_error_response(
                context,
                response,
                exc,
                grpc.StatusCode.INTERNAL,
                user_msg="Oops! Something went wrong. Please try again later.",
                error_type="UNKNOWN",
            )
