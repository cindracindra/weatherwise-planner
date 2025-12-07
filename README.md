# SSE TP1 - Event Calendar

## Name

Event Calendar Web Application

## Description

Event Calendar is a WebApp built to provide scheduling and planning capabilities for individuals. Users would be able to plan activities and events in advance using real-time weather and environmental data for improved productivity and time management.

See the full list of planned and completed features in [Roadmap](#roadmap).

If you notice any bugs or issues with this project, report them using the [Issue Tracker](#support).

We welcome any and all contributions to this project. Please follow the steps listed in our [Ways of Working](#contributing) section.

## Architecture

### High-Level Diagram

<img src="./diagrams/architecture.svg" alr="HLD" width="500">

### Database Schema

<img src="./diagrams/db-schema.png" alt="DB Schema" width="500">

## Badges

[On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.]

## Visuals

### Landing Page
<img src="./diagrams/landing_page.png" alt="Landing Page" width="500">
The landing page presents the monthly calendar with weather icons and event badges displayed on each day. Next to the calendar, the daily timetable shows all events for that day along with hourly temperature data. A profile selection dropdown and a persistent navigation bar are also visible, supporting smooth transitions across the application.

### Event Management Page
<img src="./diagrams/event_management_page.png" alt="Event Management Page" width="500">
The event management page displays a list of all events on the left, allowing users to select an event for editing. On the right, the form for creating or updating events is shown, enabling full modification of event details. Flash messages will appear at the top of the page, providing feedback on the success or failure of user actions.

### Profile Management Page
<img src="./diagrams/profile_managment_page.png" alt="Profile Management Page" width="500">
The profile management page lists all existing profiles and provides a form for creating new ones. Users can add or delete profiles directly from this interface. Flash messages will confirm the results of profile operations, ensuring clear and immediate feedback.

## Installation

[Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.]

## User Guide

This application consists of three main pages, accessible through the persistent navigation bar at the top of the interface:

### 1. Landing Page (/)

- Landing page displays a monthly calendar with event badges and weather icons for each day.
- Profile dropdown at the top allows users to filter events by profile, automatically updating both the calendar and the daily timetable.
- Manage Profiles navigation button routes the user to the Profile Management Page, where they can create and delete profiles.
- Manage Events navigation button routes the user to the Event Management Page, where they can create, edit, and delete events; this button is only accessible once a profile has been selected.

### 2. Event Management Page (/management/event)

- The left panel lists all events booked under the selected profile.
- Users can edit an event by clicking it in the left panel, which populates the form on the right panel; changes can then be updated and submitted.
- The Create Event button opens an empty form with all necessary fields to create a new event.
- Each event in the list has a Delete button to remove it from the system.
- Flash messages appear at the top of the page after creating, updating, or deleting an event to provide feedback on the action.

### 3. Profile Management Page (/management/profile)

- Users can create new profiles using the Create Profile form.
- A selected profile can be deleted from the dropdown list using the Delete Profile button.
- Flash messages appear at the top of the page to confirm the success or failure of all profile operations.

#### Navigation Summary: 

Home → Returns to the landing page
Manage Events → Open the event management interface
Manage Profiles → Open the profile management interface

The application is fully server-rendered; each action reloads the page to reflect updated data. Profile selection is preserved automatically across pages.

## Support

Please raise any issues or bugs detected via our issue tracker [here](https://gitlab.doc.ic.ac.uk/msc-software-systems-engineering/sse-tp1/-/issues).

## Roadmap

- [ ] Monthly Calendar Overview
- [ ] Real-time Weather Feed on Calendar
- [ ] Event Management (Create & Delete)
- [ ] Event Management (Update)
- [ ] Display Events on Calendar

## Contributing

All contributors to this project should follow the following ways-of-working to ensure effective communication and collaboration.

- Create a new issue, task, or incident on our issue tracker [here](https://gitlab.doc.ic.ac.uk/msc-software-systems-engineering/sse-tp1/-/issues).
- Populate the ticket with the appropriate information and tag.
- Assign the ticket for someone to work on (this can also be done by Owners and Maintainers).
- From the ticket, create a new merge request. This also creates a new branch and you can make any changes there.
- Perform the relevant tests to ensure the new changes do not break existing functionality or intorduce new bugs.
- Once completed, create a pull/merge request to master branch.
- Assign a verified Owner or Maintainer to approve your pull/merge request.
- Once approved, your changes will be deployed via the automated deployment pipeline.

Thank you for contributing to this project!

## Authors

- De Jun Tan (dt525)
- Cindra (cc4625)
- Richard Lee (rl1625)
- Timothy Ho (tyh25)

## License

[For open source projects, say how it is licensed.]

## Project status

Active

## Calendar_Service and Weather_Service Usage

### Calendar Service

#### `get_full_calendar(year: int, month: int) -> CalendarMonth`

Returns a complete calendar month with weather and holiday data.

**Data Structure:**

```python
CalendarMonth(
    year=2025,
    month=12,
    weeks=[CalendarWeek, ...],
    current_day=2  # Current day number if in this month, otherwise 0
)

CalendarWeek(
    days=[CalendarDay, ...]
)

CalendarDay(
    day=1,  # Day of month
    holidays=["Christmas"],  # List of holiday names
    weather=WeatherCode(
        code=3,
        icon="cloudy.svg",
        label="Cloudy"
    )
)
```

**Usage Example:**

```python
from services.calendar_service import get_full_calendar

# Get calendar data
calendar_month = get_full_calendar(2025, 12)
calendar_month = calendar_month.to_dict()

# Access calendar matrix (list of weeks)
calendar_matrix = calendar_month['weeks']
# Structure: [
#   [{day: 1, holidays: ["Christmas"], weather: {code: 3, icon: "cloudy.svg", label: "Cloudy"}}, ...],  # Week 1
#   [{day: 8, holidays: [], weather: {code: 1, icon: "sunny.svg", label: "Sunny"}}, ...],              # Week 2
#   ...
# ]

# Get current day for highlighting
highlight_day = calendar_month['current_day']

# Display month and year
year = calendar_month['year']
month = calendar_month['month']
```

#### `get_daily_forecast() -> Dict[str, WeatherCode]`

Returns weather forecasts for the next 7 days, mapped by date strings.

**Returns:** Dictionary with date strings (YYYY-MM-DD) as keys and WeatherCode objects as values.

**Note:** Called internally by `calendar_service.py` to populate weather data for calendar days.

### Weather Service

#### `get_hourly_forecast_today() -> List[WeatherReading]`

Returns hourly weather forecast for the current day (24 entries).

**Data Structure:**

```python
WeatherReading(
    temperature=15,
    weather=WeatherCode(
        code=1,
        icon="sunny.svg",
        label="Sunny"
    )
)
```

**Usage Example:**

```python
from services.weather_service import get_hourly_forecast_today

# Get hourly forecast
hourly_forecast = get_hourly_forecast_today()
hourly_forecast = [reading.to_dict() for reading in hourly_forecast]

# Result: [
#   {"temperature": 15, "code": 1, "icon": "sunny.svg", "label": "Sunny"},
#   {"temperature": 14, "code": 2, "icon": "partly_cloudy.svg", "label": "Partly Cloudy"},
#   ...
# ]
```

#### `get_current_weather() -> WeatherReading`

Returns the current weather conditions.

**Usage Example:**

```python
from services.weather_service import get_current_weather

# Get current weather
current_weather = get_current_weather()
current_weather = current_weather.to_dict()

# Result: {
#   "temperature": 16,
#   "code": 2,
#   "icon": "partly_cloudy.svg",
#   "label": "Partly Cloudy"
# }
```
