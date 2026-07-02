# Delta for Wash Pricing Config

## ADDED Requirements

### Requirement: Configure wash vehicle types and prices

Affected repos: Desktop, API, Mobile.
The system MUST allow authorized users to configure wash vehicle types, wash labels, active state, and wash prices used for lavado pricing.

#### Scenario: Active wash type is used for new wash

- GIVEN an active wash vehicle type has a configured price
- WHEN an operator starts a lavado using that type
- THEN the system MUST use that configured wash price
- AND it MUST snapshot the label and value on the wash operation

#### Scenario: Referenced wash type is removed

- GIVEN a wash vehicle type has historical wash usage
- WHEN an authorized user removes it
- THEN the system MUST deactivate it instead of deleting historical references

### Requirement: Keep parking tariffs independent from vehicle size

Affected repos: Desktop, API, Mobile.
Configurable vehicle types and prices MUST apply to washes only; parking estadía tariffs MUST remain independent of vehicle size.

#### Scenario: Parking stay uses configured parking tariff

- GIVEN wash vehicle types have different prices
- WHEN a parking salida or parking quote is calculated
- THEN the parking amount MUST be based on parking tariff configuration
- AND it MUST NOT use wash vehicle type price

## MODIFIED Requirements

## REMOVED Requirements
