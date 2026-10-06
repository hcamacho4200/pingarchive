"""Plugins API router"""

import logging

from fastapi import APIRouter, HTTPException

from api.request_context import build_meta, request_meta_context
from api.schema.api_response_schema import ApiResponse
from api.schema.ping_destinations_schema import PingDestinationsSchema, PingDestinationWriteSchema
from db import Database
from db.models.ping_destinations_model import PingDestinationsModel
from enums.address_type import AddressTypeEnum
from enums.location_zones import LocationZonesEnum
from enums.ping_interval import PingIntervalEnum

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ping_destinations", tags=["ping_destinations"])


def _to_schema(item: PingDestinationsModel) -> PingDestinationsSchema:
    """Convert a database record to the public API schema."""
    return PingDestinationsSchema(
        id=item.id,
        name=item.name,
        ipv4=item.ipv4,
        ipv6=item.ipv6,
        host=item.host,
        address_type=AddressTypeEnum(item.address_type),
        location_zone=LocationZonesEnum(item.location_zone),
        ping_interval=PingIntervalEnum(item.ping_interval),
        enabled=item.enabled,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", summary="Get list configured ping destinations", response_model=ApiResponse[list[PingDestinationsSchema]])
def ping_destinations():
    """Get list of configured ping destinations"""
    data_list: list[PingDestinationsModel]
    with request_meta_context() as meta:
        dbp = Database()
        with dbp.session_context_read() as session:
            try:
                data_list = PingDestinationsModel.get_list(session)
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=500, detail=str(e)) from e
    return ApiResponse(
        meta=build_meta(meta),
        data=[_to_schema(item) for item in data_list],
    )


@router.post("", summary="Create a ping destination", response_model=ApiResponse[PingDestinationsSchema], status_code=201)
def create_ping_destination(request: PingDestinationWriteSchema):
    """Create a ping destination."""
    with request_meta_context() as meta:
        dbp = Database()
        with dbp.session_context_write() as session:
            try:
                data = _to_schema(PingDestinationsModel.insert(session, **request.model_dump()))
            except Exception as exc:
                logger.exception("Unable to create ping destination")
                raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(meta=build_meta(meta), data=data)


@router.put("/{destination_id}", summary="Update a ping destination", response_model=ApiResponse[PingDestinationsSchema])
def update_ping_destination(destination_id: int, request: PingDestinationWriteSchema):
    """Update a ping destination, including its enabled state."""
    with request_meta_context() as meta:
        dbp = Database()
        with dbp.session_context_write() as session:
            try:
                data = _to_schema(PingDestinationsModel.update(session, destination_id, **request.model_dump()))
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except Exception as exc:
                logger.exception("Unable to update ping destination")
                raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(meta=build_meta(meta), data=data)


@router.delete("/{destination_id}", summary="Delete a ping destination", response_model=ApiResponse[PingDestinationsSchema])
def delete_ping_destination(destination_id: int):
    """Delete a ping destination."""
    with request_meta_context() as meta:
        dbp = Database()
        with dbp.session_context_write() as session:
            try:
                destination = PingDestinationsModel.delete(session, destination_id)
                data = _to_schema(destination)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except Exception as exc:
                logger.exception("Unable to delete ping destination")
                raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(meta=build_meta(meta), data=data)


# @router.post("/validate_config", summary="Validate a configuration value", response_model=ApiResponse[PluginAPIValidateResponse])
# def validate_config(request: PluginAPIValidateRequest):
#     """Validate a configuration value"""
#     data: PluginAPIValidateResponse
#     with request_meta_context() as meta:
#         config_key = cast(PluginConfigKey, request.config_key)
#         config_value = request.config_value
#         message: str | None = None
#         valid = True
#         try:
#             PluginConfigData.validate_config(config_key, config_value)
#         except ValueError as e:
#             message = str(e)
#             valid = False

#         data = PluginAPIValidateResponse(
#             config_key=request.config_key,
#             config_value=request.config_value,
#             valid=valid,
#             message=message,
#         )

#     return ApiResponse(meta=build_meta(meta), data=data)


# @router.get(
#     "/required_keys/{plugin_name}",
#     summary="Get list required configuration keys for a plugins",
#     response_model=ApiResponse[list[PluginAPIRequiredKeysResponse]],
# )
# def required_keys(plugin_name: str):
#     """Get list of registered plugins"""
#     data_list: list[PluginAPIRequiredKeysResponse] = []
#     with request_meta_context() as meta:
#         required_keys = PLUGIN_REGISTRY[plugin_name].required_config_keys
#         for config_key in required_keys if required_keys else []:
#             config_field = CONFIG_FIELD_REGISTRY[config_key]

#             data_list.append(
#                 PluginAPIRequiredKeysResponse(
#                     config_key=config_key,
#                     config_key_label=config_field.label,
#                     display=config_field.display,
#                 )
#             )
#     return ApiResponse(meta=build_meta(meta), data=data_list)


# @router.get("/registered", summary="Get list of registered plugins", response_model=ApiResponse[list[str]])
# def registered_plugins():
#     """Get list of registered plugins"""
#     data_list: list[str]
#     with request_meta_context() as meta:
#         data_list = list(PLUGIN_REGISTRY.keys())

#     return ApiResponse(meta=build_meta(meta), data=data_list)


# @router.delete("/{plugin_id}", summary="Delete a plugin configuration", response_model=ApiResponse[PluginAPIDataRead])
# def delete_plugin(plugin_id: int):
#     """Delete a plugin configuration"""

#     with request_meta_context() as meta:
#         dbp = Database()
#         with dbp.session_context_write() as session:
#             try:
#                 data = PluginsModel.delete(session, plugin_id)
#                 result = PluginAPIDataRead(**data.__dict__)

#             except ValueError as e:
#                 raise HTTPException(status_code=400, detail=str(e)) from e

#             except Exception as e:
#                 logger.error(e)
#                 raise HTTPException(status_code=500, detail=str(e)) from e
#     return ApiResponse(meta=build_meta(meta), data=result)


# @router.put("/{plugin_id}", summary="Update a plugin configuration", response_model=ApiResponse[PluginAPIDataRead])
# def put_plugin(plugin_id: int, request: PluginAPIDataWrite):
#     """Update a plugin configuration"""

#     with request_meta_context() as meta:
#         dbp = Database()
#         with dbp.session_context_write() as session:
#             try:
#                 plugin_rec = PluginsModel.get_by_id(session, plugin_id)
#                 config: PluginConfigData = PluginConfigData(**json.loads(plugin_rec.config) if plugin_rec.config else {})
#                 for key, value in json.loads(request.config).items():
#                     setattr(config, key, value)
#                 request.config = json.dumps(config.model_dump(context={"redact_encrypted": False}))
#                 logger.info(config.auth_api_key)

#                 data = PluginsModel.update(session, plugin_id, **request.model_dump())
#                 result = PluginAPIDataRead(**data.__dict__)
#                 result.config = config.model_dump_json()

#             except ValueError as e:
#                 raise HTTPException(status_code=400, detail=str(e)) from e

#             except Exception as e:
#                 logger.error(e)
#                 raise HTTPException(status_code=500, detail=str(e)) from e
#     return ApiResponse(meta=build_meta(meta), data=result)


# @router.post("", summary="Create a plugin configuration", response_model=ApiResponse[PluginAPIDataRead])
# def post_plugin(request: PluginAPIDataWrite):
#     """Create a plugin configuration"""

#     with request_meta_context() as meta:
#         dbp = Database()
#         with dbp.session_context_write() as session:
#             try:
#                 config: PluginConfigData = PluginConfigData()
#                 for key, value in json.loads(request.config).items():
#                     setattr(config, key, value)
#                 request.config = json.dumps(config.model_dump(context={"redact_encrypted": False}))
#                 logger.info(config.auth_api_key)

#                 data = PluginsModel.insert(session, **request.model_dump())
#                 result = PluginAPIDataRead(**data.__dict__)
#                 result.config = config.model_dump_json()
#             except Exception as e:
#                 logger.error(e)
#                 raise HTTPException(status_code=500, detail=str(e)) from e
#     return ApiResponse(meta=build_meta(meta), data=result)
