from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import CE04Entity
from .models import CE04Data


@dataclass(frozen=True, kw_only=True)
class CE04SensorDescription(SensorEntityDescription):
    value_fn: Callable[[CE04Data], object]


SENSORS: tuple[CE04SensorDescription, ...] = (
    # ---- EV battery --------------------------------------------------
    CE04SensorDescription(
        key="battery_level",
        name="Battery level",
        icon="mdi:battery-charging",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda bike: bike.battery_level,
    ),
    CE04SensorDescription(
        key="remaining_range",
        name="Remaining range",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.remaining_range_electric_km,
    ),
    # ---- Odometer / trip ---------------------------------------------
    CE04SensorDescription(
        key="total_mileage",
        name="Total mileage",
        icon="mdi:speedometer",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.total_mileage_km,
    ),
    CE04SensorDescription(
        key="trip1",
        name="Trip 1",
        icon="mdi:road-variant",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.trip1_km,
    ),
    CE04SensorDescription(
        key="trip2",
        name="Trip 2",
        icon="mdi:road-variant",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.trip2_km,
    ),
    # ---- Tyre pressures ----------------------------------------------
    CE04SensorDescription(
        key="tire_pressure_front",
        name="Tire pressure front",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda bike: bike.tire_pressure_front_bar,
    ),
    CE04SensorDescription(
        key="tire_pressure_rear",
        name="Tire pressure rear",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda bike: bike.tire_pressure_rear_bar,
    ),
    # ---- Service & Diagnostics ----------------------------------------
    CE04SensorDescription(
        key="vin",
        name="VIN",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.vin,
    ),
    CE04SensorDescription(
        key="sw_version",
        name="Software version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: str(bike.raw.get("_version")) if bike.raw.get("_version") is not None else None,
    ),
    CE04SensorDescription(
        key="next_service_due_date",
        name="Next service due date",
        icon="mdi:wrench-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.next_service_due_date,
    ),
    CE04SensorDescription(
        key="next_service_remaining_distance",
        name="Next service remaining distance",
        icon="mdi:wrench-outline",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.next_service_remaining_distance_km,
    ),
    # ---- Connectivity (diagnostic) -----------------------------------
    CE04SensorDescription(
        key="last_connected_time",
        name="Last connected time",
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.last_connected_time,
    ),
    CE04SensorDescription(
        key="last_activated_time",
        name="Last activated time",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.last_activated_time,
    ),
    CE04SensorDescription(
        key="charging_time_estimation",
        name="Charging time estimation",
        icon="mdi:battery-clock",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.charging_time_estimation_electric,
    ),
    CE04SensorDescription(
        key="battery_soh",
        name="Battery maximum capacity",
        icon="mdi:battery-heart-variant",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda bike: bike.soc_max_electric,
    ),
)


class CE04Sensor(CE04Entity, SensorEntity):
    entity_description: CE04SensorDescription

    def __init__(
        self,
        coordinator,
        bike_id: str,
        description: CE04SensorDescription,
    ) -> None:
        super().__init__(coordinator, bike_id)
        self.entity_description = description
        self._attr_unique_id = f"v1_{self.bike_slug}_{description.key}"
        self._attr_suggested_object_id = f"{self.bike_slug}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.bike)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        CE04Sensor(coordinator, bike_id, description)
        for bike_id in coordinator.data
        for description in SENSORS
    ]
    async_add_entities(entities)
