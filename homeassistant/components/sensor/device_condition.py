"""Provides device conditions for sensors."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation.exceptions import (
    InvalidDeviceAutomationConfig,
)
from homeassistant.const import CONF_ABOVE, CONF_BELOW, CONF_ENTITY_ID, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import condition, config_validation as cv
from homeassistant.helpers.entity import get_device_class, get_unit_of_measurement
from homeassistant.helpers.entity_registry import (
    async_entries_for_device,
    async_get_registry,
)
from homeassistant.helpers.typing import ConfigType

from . import DOMAIN, SensorDeviceClass

# mypy: allow-untyped-defs, no-check-untyped-defs

DEVICE_CLASS_NONE = "none"

CONF_IS_APPARENT_POWER = "is_apparent_power"
CONF_IS_BATTERY_LEVEL = "is_battery_level"
CONF_IS_CO = "is_carbon_monoxide"
CONF_IS_CO2 = "is_carbon_dioxide"
CONF_IS_CURRENT = "is_current"
CONF_IS_ENERGY = "is_energy"
CONF_IS_FREQUENCY = "is_frequency"
CONF_IS_HUMIDITY = "is_humidity"
CONF_IS_GAS = "is_gas"
CONF_IS_ILLUMINANCE = "is_illuminance"
CONF_IS_NITROGEN_DIOXIDE = "is_nitrogen_dioxide"
CONF_IS_NITROGEN_MONOXIDE = "is_nitrogen_monoxide"
CONF_IS_NITROUS_OXIDE = "is_nitrous_oxide"
CONF_IS_OZONE = "is_ozone"
CONF_IS_PM1 = "is_pm1"
CONF_IS_PM10 = "is_pm10"
CONF_IS_PM25 = "is_pm25"
CONF_IS_POWER = "is_power"
CONF_IS_POWER_FACTOR = "is_power_factor"
CONF_IS_PRESSURE = "is_pressure"
CONF_IS_REACTIVE_POWER = "is_reactive_power"
CONF_IS_SIGNAL_STRENGTH = "is_signal_strength"
CONF_IS_SULPHUR_DIOXIDE = "is_sulphur_dioxide"
CONF_IS_TEMPERATURE = "is_temperature"
CONF_IS_VOLATILE_ORGANIC_COMPOUNDS = "is_volatile_organic_compounds"
CONF_IS_VOLTAGE = "is_voltage"
CONF_IS_VALUE = "is_value"

ENTITY_CONDITIONS = {
    SensorDeviceClass.APPARENT_POWER: [{CONF_TYPE: CONF_IS_APPARENT_POWER}],
    SensorDeviceClass.BATTERY: [{CONF_TYPE: CONF_IS_BATTERY_LEVEL}],
    SensorDeviceClass.CO: [{CONF_TYPE: CONF_IS_CO}],
    SensorDeviceClass.CO2: [{CONF_TYPE: CONF_IS_CO2}],
    SensorDeviceClass.CURRENT: [{CONF_TYPE: CONF_IS_CURRENT}],
    SensorDeviceClass.ENERGY: [{CONF_TYPE: CONF_IS_ENERGY}],
    SensorDeviceClass.FREQUENCY: [{CONF_TYPE: CONF_IS_FREQUENCY}],
    SensorDeviceClass.GAS: [{CONF_TYPE: CONF_IS_GAS}],
    SensorDeviceClass.HUMIDITY: [{CONF_TYPE: CONF_IS_HUMIDITY}],
    SensorDeviceClass.ILLUMINANCE: [{CONF_TYPE: CONF_IS_ILLUMINANCE}],
    SensorDeviceClass.NITROGEN_DIOXIDE: [{CONF_TYPE: CONF_IS_NITROGEN_DIOXIDE}],
    SensorDeviceClass.NITROGEN_MONOXIDE: [{CONF_TYPE: CONF_IS_NITROGEN_MONOXIDE}],
    SensorDeviceClass.NITROUS_OXIDE: [{CONF_TYPE: CONF_IS_NITROUS_OXIDE}],
    SensorDeviceClass.OZONE: [{CONF_TYPE: CONF_IS_OZONE}],
    SensorDeviceClass.POWER: [{CONF_TYPE: CONF_IS_POWER}],
    SensorDeviceClass.POWER_FACTOR: [{CONF_TYPE: CONF_IS_POWER_FACTOR}],
    SensorDeviceClass.PM1: [{CONF_TYPE: CONF_IS_PM1}],
    SensorDeviceClass.PM10: [{CONF_TYPE: CONF_IS_PM10}],
    SensorDeviceClass.PM25: [{CONF_TYPE: CONF_IS_PM25}],
    SensorDeviceClass.PRESSURE: [{CONF_TYPE: CONF_IS_PRESSURE}],
    SensorDeviceClass.REACTIVE_POWER: [{CONF_TYPE: CONF_IS_REACTIVE_POWER}],
    SensorDeviceClass.SIGNAL_STRENGTH: [{CONF_TYPE: CONF_IS_SIGNAL_STRENGTH}],
    SensorDeviceClass.SULPHUR_DIOXIDE: [{CONF_TYPE: CONF_IS_SULPHUR_DIOXIDE}],
    SensorDeviceClass.TEMPERATURE: [{CONF_TYPE: CONF_IS_TEMPERATURE}],
    SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: [
        {CONF_TYPE: CONF_IS_VOLATILE_ORGANIC_COMPOUNDS}
    ],
    SensorDeviceClass.VOLTAGE: [{CONF_TYPE: CONF_IS_VOLTAGE}],
    DEVICE_CLASS_NONE: [{CONF_TYPE: CONF_IS_VALUE}],
}

CONDITION_SCHEMA = vol.All(
    cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
        {
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Required(CONF_TYPE): vol.In(
                [
                    CONF_IS_APPARENT_POWER,
                    CONF_IS_BATTERY_LEVEL,
                    CONF_IS_CO,
                    CONF_IS_CO2,
                    CONF_IS_CURRENT,
                    CONF_IS_ENERGY,
                    CONF_IS_FREQUENCY,
                    CONF_IS_GAS,
                    CONF_IS_HUMIDITY,
                    CONF_IS_ILLUMINANCE,
                    CONF_IS_OZONE,
                    CONF_IS_NITROGEN_DIOXIDE,
                    CONF_IS_NITROGEN_MONOXIDE,
                    CONF_IS_NITROUS_OXIDE,
                    CONF_IS_POWER,
                    CONF_IS_POWER_FACTOR,
                    CONF_IS_PM1,
                    CONF_IS_PM10,
                    CONF_IS_PM25,
                    CONF_IS_PRESSURE,
                    CONF_IS_REACTIVE_POWER,
                    CONF_IS_SIGNAL_STRENGTH,
                    CONF_IS_SULPHUR_DIOXIDE,
                    CONF_IS_TEMPERATURE,
                    CONF_IS_VOLATILE_ORGANIC_COMPOUNDS,
                    CONF_IS_VOLTAGE,
                    CONF_IS_VALUE,
                ]
            ),
            vol.Optional(CONF_BELOW): vol.Any(vol.Coerce(float)),
            vol.Optional(CONF_ABOVE): vol.Any(vol.Coerce(float)),
        }
    ),
    cv.has_at_least_one_key(CONF_BELOW, CONF_ABOVE),
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions."""
    conditions: list[dict[str, str]] = []
    entity_registry = await async_get_registry(hass)
    entries = [
        entry
        for entry in async_entries_for_device(entity_registry, device_id)
        if entry.domain == DOMAIN
    ]

    for entry in entries:
        device_class = get_device_class(hass, entry.entity_id) or DEVICE_CLASS_NONE
        unit_of_measurement = get_unit_of_measurement(hass, entry.entity_id)

        if not unit_of_measurement:
            continue

        templates = ENTITY_CONDITIONS.get(
            device_class, ENTITY_CONDITIONS[DEVICE_CLASS_NONE]
        )

        conditions.extend(
            {
                **template,
                "condition": "device",
                "device_id": device_id,
                "entity_id": entry.entity_id,
                "domain": DOMAIN,
            }
            for template in templates
        )

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Evaluate state based on configuration."""
    numeric_state_config = {
        condition.CONF_CONDITION: "numeric_state",
        condition.CONF_ENTITY_ID: config[CONF_ENTITY_ID],
    }
    if CONF_ABOVE in config:
        numeric_state_config[condition.CONF_ABOVE] = config[CONF_ABOVE]
    if CONF_BELOW in config:
        numeric_state_config[condition.CONF_BELOW] = config[CONF_BELOW]

    numeric_state_config = cv.NUMERIC_STATE_CONDITION_SCHEMA(numeric_state_config)
    numeric_state_config = condition.numeric_state_validate_config(
        hass, numeric_state_config
    )
    return condition.async_numeric_state_from_config(numeric_state_config)


async def async_get_condition_capabilities(hass, config):
    """List condition capabilities."""
    try:
        unit_of_measurement = get_unit_of_measurement(hass, config[CONF_ENTITY_ID])
    except HomeAssistantError:
        unit_of_measurement = None

    if not unit_of_measurement:
        raise InvalidDeviceAutomationConfig(
            "No unit of measurement found for condition entity {config[CONF_ENTITY_ID]}"
        )

    return {
        "extra_fields": vol.Schema(
            {
                vol.Optional(
                    CONF_ABOVE, description={"suffix": unit_of_measurement}
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_BELOW, description={"suffix": unit_of_measurement}
                ): vol.Coerce(float),
            }
        )
    }
