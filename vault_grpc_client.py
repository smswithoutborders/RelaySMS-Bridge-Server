"""
Vault gRPC Client.

This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

import functools
import grpc

import vault_pb2
import vault_pb2_grpc

from utils import get_logger, get_env_var, mask_sensitive_info

logger = get_logger(__name__)


def get_channel(internal=True):
    """Get the appropriate gRPC channel based on the mode.

    Args:
        internal (bool, optional): Flag indicating whether to use internal ports.
            Defaults to True.

    Returns:
        grpc.Channel: The gRPC channel.
    """
    mode = get_env_var("MODE", default_value="development")
    hostname = get_env_var("VAULT_GRPC_HOST")
    if internal:
        port = get_env_var("VAULT_GRPC_INTERNAL_PORT")
        secure_port = get_env_var("VAULT_GRPC_INTERNAL_SSL_PORT")
    else:
        port = get_env_var("VAULT_GRPC_PORT")
        secure_port = get_env_var("VAULT_GRPC_SSL_PORT")

    if mode == "production":
        logger.info("Connecting to vault gRPC server at %s:%s", hostname, secure_port)
        credentials = grpc.ssl_channel_credentials()
        logger.info("Using secure channel for gRPC communication")
        return grpc.secure_channel(f"{hostname}:{secure_port}", credentials)

    logger.info("Connecting to vault gRPC server at %s:%s", hostname, port)
    logger.warning("Using insecure channel for gRPC communication")
    return grpc.insecure_channel(f"{hostname}:{port}")


def grpc_call(internal=True):
    """Decorator to handle gRPC calls."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                channel = get_channel(internal)

                with channel as conn:
                    kwargs["stub"] = (
                        vault_pb2_grpc.EntityInternalStub(conn)
                        if internal
                        else vault_pb2_grpc.EntityStub(conn)
                    )
                    return func(*args, **kwargs)
            except grpc.RpcError as e:
                return None, e
            except Exception as e:
                raise e

        return wrapper

    return decorator


@grpc_call()
def decrypt_payload(phone_number, payload_ciphertext, **kwargs):
    """
    Sends a request to decrypt the provided payload ciphertext.

    Args:
        phone_number (str): The phone number associated with the bridge entity.
        payload_ciphertext (str): The encrypted payload to be decrypted.
        **kwargs:
            - stub (object): The gRPC client stub for making the request.

    Returns:
        tuple: A tuple containing:
            - response (object): The vault server's response.
            - error (Exception or None): None if successful, otherwise the encountered exception.
    """
    stub = kwargs["stub"]

    request = vault_pb2.DecryptPayloadRequest(
        payload_ciphertext=payload_ciphertext,
        phone_number=phone_number,
    )

    identifier = mask_sensitive_info(phone_number)

    logger.debug("Initiating decryption request using phone_number='%s'.", identifier)

    response = stub.DecryptPayload(request)

    logger.info(
        "Decryption successful using identifier type: phone_number.",
    )
    return response, None


@grpc_call()
def encrypt_payload(phone_number, payload_plaintext, **kwargs):
    """
    Sends a request to encrypt the provided plaintext payload.

    Args:
        phone_number (str): The phone number associated with the bridge entity.
        payload_plaintext (str): The plaintext payload to be encrypted.
        **kwargs:
            - stub (object): The gRPC client stub for making the request.

    Returns:
        tuple: A tuple containing:
            - response (object): The vault server's response.
            - error (Exception or None): None if successful, otherwise the encountered exception.
    """
    stub = kwargs["stub"]

    request = vault_pb2.EncryptPayloadRequest(
        phone_number=phone_number,
        payload_plaintext=payload_plaintext,
    )

    logger.debug(
        "Initiating encryption request using phone_number='%s'.",
        mask_sensitive_info(phone_number),
    )

    response = stub.EncryptPayload(request)

    logger.info("Encryption successful using phone_number.")

    return response, None


@grpc_call()
def create_bridge_entity(phone_number, **kwargs):
    """
    Sends a request to create a bridge entity.

    Args:
        phone_number (str): The phone number associated with the bridge entity.
        **kwargs:
            - stub (object): The gRPC client stub for making requests.
            - country_code (str, optional): The country code for the phone number.
            - client_publish_pub_key (str, optional): The client's public key used for publishing.
            - ownership_proof_response (str, optional): Proof of ownership response.

    Returns:
        tuple:
            - response (object): The vault server's response.
            - error (Exception or None): None if successful, otherwise the encountered exception.
    """
    stub = kwargs["stub"]
    country_code = kwargs.get("country_code")
    client_publish_pub_key = kwargs.get("client_publish_pub_key")
    ownership_proof_response = kwargs.get("ownership_proof_response")
    server_pub_key_identifier = kwargs.get("server_pub_key_identifier")

    request = vault_pb2.CreateBridgeEntityRequest(
        phone_number=phone_number,
        country_code=country_code,
        client_publish_pub_key=client_publish_pub_key,
        ownership_proof_response=ownership_proof_response,
        server_pub_key_identifier=server_pub_key_identifier,
    )

    logger.debug(
        "Sending request to create bridge entity for phone_number: %s",
        phone_number,
    )
    response = stub.CreateBridgeEntity(request)
    logger.info("Successfully created bridge entity.")
    return response, None


@grpc_call()
def authenticate_bridge_entity(phone_number, **kwargs):
    """
    Sends a request to authenticate a bridge entity.

    Args:
        phone_number (str): The phone number associated with the bridge entity.
        **kwargs:
            - stub (object): The gRPC client stub for making requests.

    Returns:
        tuple: A tuple containing:
            - response (object): The vault server's response.
            - error (Exception or None): None if successful, otherwise the encountered exception.
    """
    stub = kwargs["stub"]

    request = vault_pb2.AuthenticateBridgeEntityRequest(phone_number=phone_number)

    logger.debug(
        "Sending request to authenticate bridge entity for phone_number: %s",
        phone_number,
    )
    response = stub.AuthenticateBridgeEntity(request)
    logger.info("Successfully authenticated bridge entity.")
    return response, None
