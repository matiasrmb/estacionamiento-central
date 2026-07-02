# Delta for Pricing Quotes

## ADDED Requirements

### Requirement: Quote parking, washes, monthly plans, and combinations

Affected repos: Desktop, API.
The system MUST provide quote previews for parking estadía, lavados, mensualidad, and combinations without creating billable operations.

#### Scenario: Operator quotes a combined service

- GIVEN an operator enters quote inputs for estadía and lavado
- WHEN the quote is calculated
- THEN the system MUST show itemized amounts for each selected service
- AND the preview MUST NOT create an ingreso, lavado, cierre item, or payment record

#### Scenario: Operator quotes parking by vehicle size

- GIVEN an operator selects a vehicle size while quoting parking estadía
- WHEN the quote is calculated
- THEN parking price MUST use parking tariff rules only
- AND parking price MUST NOT vary by vehicle size

### Requirement: Quote monthly plans for multiple vehicles

Affected repos: Desktop, API.
Monthly quotes MUST support multiple vehicles and show total monthly amount, daily cost per vehicle, and combined daily total.

#### Scenario: Monthly quote includes multiple vehicles

- GIVEN an operator enters two or more monthly vehicles with monthly amounts
- WHEN the monthly quote is calculated
- THEN the system MUST show each vehicle daily cost
- AND it MUST show combined monthly total and combined daily total

#### Scenario: Monthly quote has missing vehicle amount

- GIVEN a monthly vehicle has no configured or entered amount
- WHEN the operator requests a quote
- THEN the system MUST require an amount or show that the vehicle cannot be quoted

## MODIFIED Requirements

## REMOVED Requirements
