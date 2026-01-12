"""
Visier Aggregate Query Implementation

RESTful API-based aggregate queries for Visier Platform (no SDK dependencies).

Core functions:
    - execute_vanilla_aggregate_query() - Execute aggregate queries
    - convert_vanilla_response_to_dataframe() - Convert responses to DataFrames
    - Helper functions for building queries (create_dimension_axis, create_member_set_filter, etc.)

Usage:
    from aggregate.aggregate_query_vanilla import (
        execute_vanilla_aggregate_query,
        convert_vanilla_response_to_dataframe,
        create_dimension_axis
    )
    
    # Build and execute query
    axes = [create_dimension_axis("Function")]
    response = execute_vanilla_aggregate_query(metric_id="employeeCount", axes=axes)
    df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_api_config() -> Dict[str, str]:
    """
    Get API configuration from environment variables.
    
    Returns:
        Dictionary with host, apikey, vanity, username, password
    """
    required_vars = [
        "VISIER_HOST",
        "VISIER_APIKEY",
        "VISIER_VANITY",
        "VISIER_USERNAME",
        "VISIER_PASSWORD"
    ]
    
    config = {}
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var.lower().replace("visier_", "")] = value
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set these in your .env file. See visier.env.example for a template."
        )
    
    return config


def create_dimension_axis(
    dimension_name: str,
    qualifying_path: str = "Employee",
    level_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Helper function to create a dimension axis easily.
    
    For parent-child dimensions (like Organization_Hierarchy), you need to specify
    actual level IDs. Common patterns:
    - ["Level_1", "Level_2", "Level_3"] (generic levels)
    - ["Profit_Center", "Business_Unit", "Department"] (named levels)
    - [dimension_name] (sometimes the dimension name itself works)
    
    To discover available level IDs, you may need to:
    1. Check your Visier tenant's data model documentation
    2. Use the Dimensions API to list available levels
    3. Try common level ID patterns
    
    Args:
        dimension_name: Name of the dimension (e.g., "Function", "Organization_Hierarchy")
        qualifying_path: Qualifying path (default: "Employee")
        level_ids: List of level IDs to use. If None, uses [dimension_name] for regular dimensions.
                   For parent-child dimensions, you MUST specify actual level IDs.
    
    Returns:
        Axis dictionary ready to use in query
    
    Example:
        # Regular dimension
        axis = create_dimension_axis("Function")
        
        # Parent-child dimension - try dimension name first
        axis = create_dimension_axis("Organization_Hierarchy", level_ids=["Organization_Hierarchy"])
        
        # Parent-child dimension - specific levels (if you know them)
        axis = create_dimension_axis("Organization_Hierarchy", level_ids=["Profit_Center", "Business_Unit"])
    """
    if level_ids is None:
        # Default: use dimension name as level ID (works for regular dimensions)
        level_ids = [dimension_name]
    
    dimension_dict = {"name": dimension_name}
    if qualifying_path:
        dimension_dict["qualifyingPath"] = qualifying_path
    
    return {
        "dimensionLevelSelection": {
            "dimension": dimension_dict,
            "levelIds": level_ids
        }
    }


def create_member_set_filter(
    dimension_name: str,
    included_members: Optional[List[str]] = None,
    excluded_members: Optional[List[str]] = None,
    qualifying_path: str = "Employee"
) -> Dict[str, Any]:
    """
    Create a member set filter to filter by specific dimension members.
    
    This allows you to focus on specific members of a dimension (e.g., only certain Functions).
    
    Args:
        dimension_name: Name of the dimension (e.g., "Function")
        included_members: List of member names to include (e.g., ["Engineering", "Sales"])
                          If None, includes all members
        excluded_members: List of member names to exclude
                          If None, excludes nothing
        qualifying_path: Qualifying path (default: "Employee")
    
    Returns:
        Filter dictionary ready to use in query
    
    Example:
        # Only include Engineering and Sales functions
        filter = create_member_set_filter("Function", included_members=["Engineering", "Sales"])
        
        # Exclude specific functions
        filter = create_member_set_filter("Function", excluded_members=["HR"])
    """
    filter_dict = {
        "memberSet": {
            "dimension": {
                "name": dimension_name,
                "qualifyingPath": qualifying_path
            },
            "values": {}
        }
    }
    
    if included_members:
        filter_dict["memberSet"]["values"]["included"] = [
            {"path": [member]} for member in included_members
        ]
    
    if excluded_members:
        filter_dict["memberSet"]["values"]["excluded"] = [
            {"path": [member]} for member in excluded_members
        ]
    
    return filter_dict


def create_selection_concept_filter(concept_name: str, qualifying_path: str = "Employee") -> Dict[str, Any]:
    """
    Create a selection concept filter (e.g., isManager, isActive).
    
    Args:
        concept_name: Name of the selection concept (e.g., "isManager")
        qualifying_path: Qualifying path (default: "Employee")
    
    Returns:
        Filter dictionary ready to use in query
    
    Example:
        # Filter to only managers
        filter = create_selection_concept_filter("isManager")
    """
    return {
        "selectionConcept": {
            "name": concept_name,
            "qualifyingPath": qualifying_path
        }
    }


def create_time_axis(
    time_dimension_name: str = "Time",
    time_level_id: str = "FISCAL_YEAR",
    qualifying_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Time dimension axis for time-based grouping (e.g., fiscal years).
    
    This is used when you want Time as a column/row dimension (e.g., FY 2022, FY 2023, etc.)
    rather than just filtering by time period.
    
    NOTE: The exact dimension name and level ID may vary by tenant.
    Common options:
    - Dimension name: "Time", "Fiscal_Year", "Calendar_Year"
    - Level ID: "FISCAL_YEAR", "YEAR", "FiscalYear", "CalendarYear"
    - Qualifying path: May not be needed for Time dimension (try None first)
    
    Args:
        time_dimension_name: Name of the Time dimension (default: "Time")
        time_level_id: Level ID for the time period (default: "FISCAL_YEAR")
        qualifying_path: Qualifying path (default: None - try without first)
    
    Returns:
        Axis dictionary for Time dimension
    
    Example:
        # Use Time as a dimension to get yearly breakdown
        time_axis = create_time_axis("Time", "FISCAL_YEAR")
    """
    dimension_dict = {"name": time_dimension_name}
    if qualifying_path:
        dimension_dict["qualifyingPath"] = qualifying_path
    
    return {
        "dimensionLevelSelection": {
            "dimension": dimension_dict,
            "levelIds": [time_level_id]
        }
    }


def build_vanilla_aggregate_query(
    metric_id: str,
    axes: Optional[List[Dict[str, Any]]] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    time_intervals: Optional[Dict[str, Any]] = None,
    parameter_values: Optional[List[Dict[str, Any]]] = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build an aggregate query payload matching the API reference exactly.
    
    Args:
        metric_id: The metric ID to query (e.g., "employeeCount")
        axes: List of axis definitions for grouping. **REQUIRED for aggregate queries.**
              Format: [{"dimensionLevelSelection": {"dimension": {"name": "Gender", "qualifyingPath": "Employee"}, "levelIds": ["Gender"]}}]
        filters: Optional list of filter definitions.
                 Format: [{"selectionConcept": {"name": "isManager", "qualifyingPath": "Employee"}}]
        time_intervals: Optional time interval specification.
                        Both "intervalCount" and "intervalPeriodCount" are valid.
                        Simple: {"intervalCount": 3, "dynamicDateFrom": "SOURCE"}
                        Explicit: {"fromDateTime": "2021-01-01", "intervalPeriodType": "MONTH", "intervalCount": 6}
        parameter_values: Optional parameter values for parameterized metrics.
        options: Optional query options.
                 Common: {"zeroVisibility": "ELIMINATE", "nullVisibility": "ELIMINATE"}
    
    Returns:
        Complete query payload matching API reference schema
    
    Raises:
        ValueError: If axes are not provided (required for aggregate queries)
    """
    if not axes:
        raise ValueError(
            "Aggregate queries require at least one axis (dimension). "
            "Please provide axes parameter with at least one dimension."
        )
    
    query = {
        "source": {
            "metric": metric_id
        },
        "axes": axes
    }
    
    # Add optional components
    if filters:
        query["filters"] = filters
    
    if time_intervals:
        query["timeIntervals"] = time_intervals
    
    if parameter_values:
        query["parameterValues"] = parameter_values
    
    payload = {
        "query": query
    }
    
    if options:
        payload["options"] = options
    
    return payload




def get_asid_token(config: Optional[Dict[str, str]] = None) -> str:
    """
    Get an ASID authentication token using username/password.
    
    Based on Postman collection pattern:
    - Endpoint: POST /v1/admin/visierSecureToken
    - Headers: Content-Type: application/x-www-form-urlencoded
    - Body: form data with username and password
    - Response: ASID token (may be JSON with 'asid' field or plain string)
    
    Args:
        config: Optional API config dict. If None, loads from environment.
    
    Returns:
        ASID token string
    
    Raises:
        ValueError: If required parameters are missing
        requests.HTTPError: If authentication fails
    """
    if config is None:
        config = get_api_config()
    
    # Build the authentication URL (Postman collection pattern)
    host = config["host"].rstrip('/')
    vanity = config["vanity"]
    url = f"{host}/v1/admin/visierSecureToken"
    
    # Prepare headers (Postman collection pattern)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # Add API key if provided (some endpoints require it)
    if config.get("apikey"):
        headers["apikey"] = config["apikey"]
    
    # Prepare form data (Postman collection pattern)
    form_data = {
        "username": config["username"],
        "password": config["password"]
    }
    
    # Add vanity as query parameter or form data (check Postman collection)
    params = {}
    if vanity:
        params["vanity"] = vanity
    
    # Make the token request
    response = requests.post(
        url,
        headers=headers,
        data=form_data,  # Form-encoded data
        params=params
    )
    
    # Check for errors
    response.raise_for_status()
    
    # Parse token from response
    # Postman collection shows response may be JSON with 'asid' field or plain string
    try:
        # Try parsing as JSON first
        json_response = response.json()
        if isinstance(json_response, dict) and "asid" in json_response:
            token = json_response["asid"]
        elif isinstance(json_response, str):
            token = json_response
        else:
            # If it's a dict but no 'asid' field, try to get the token value
            token = str(json_response)
    except (ValueError, json.JSONDecodeError):
        # Not JSON, treat as plain string
        token = response.text.strip()
    
    # Clean up token (remove quotes if present)
    token = str(token).strip().strip('"').strip("'")
    return token


def load_query_payload_from_json(json_file_path: str) -> Dict[str, Any]:
    """
    Load query payload from a JSON file.
    
    The JSON file should have a "payload" key containing the query structure,
    or the payload can be at the root level.
    
    Args:
        json_file_path: Path to the JSON file containing the query payload
    
    Returns:
        Query payload dictionary ready to send to the API
    
    Example JSON structure:
        {
          "payload": {
            "query": {
              "source": {"metric": "employeeCount"},
              "axes": [...],
              ...
            }
          }
        }
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
        ValueError: If the payload structure is invalid
    """
    if not os.path.exists(json_file_path):
        raise FileNotFoundError(f"Payload file not found: {json_file_path}")
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Check if payload is nested under "payload" key
    if "payload" in data:
        return data["payload"]
    # Otherwise, assume the entire JSON is the payload
    return data


def execute_vanilla_aggregate_query(
    payload: Optional[Dict[str, Any]] = None,
    payload_file: Optional[str] = None,
    metric_id: Optional[str] = None,
    axes: Optional[List[Dict[str, Any]]] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    time_intervals: Optional[Dict[str, Any]] = None,
    parameter_values: Optional[List[Dict[str, Any]]] = None,
    options: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, str]] = None,
    asid_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute an aggregate query using vanilla HTTP requests.
    
    Flow: ASID Token (from username/password) + API Key -> Aggregate Query
    
    This bypasses the SDK entirely and makes direct HTTP calls to the Visier API,
    giving us full control over the request payload.
    
    Args:
        payload: Complete query payload dictionary. If provided, all other parameters are ignored.
        payload_file: Path to JSON file containing the query payload. If provided, loads from file.
        metric_id: The metric ID to query (only used if payload/payload_file not provided)
        axes: List of axis definitions (required if building payload from scratch)
        filters: Optional list of filter definitions
        time_intervals: Optional time interval specification
        parameter_values: Optional parameter values
        options: Optional query options
        config: Optional API config dict. If None, loads from environment.
        asid_token: Optional ASID token. If None, will fetch one automatically using username/password.
    
    Returns:
        Response JSON as dictionary (CellSetDTO structure)
    
    Raises:
        ValueError: If required parameters are missing
        requests.HTTPError: If API request fails
    
    Priority:
        1. payload (direct dict) - highest priority
        2. payload_file (JSON file path) - second priority
        3. Build from individual parameters (metric_id, axes, etc.) - fallback
    """
    if config is None:
        config = get_api_config()
    
    # Get ASID token if not provided (uses username/password from config)
    if asid_token is None:
        asid_token = get_asid_token(config)
    
    # Load or build the query payload
    if payload is not None:
        # Use provided payload directly
        query_payload = payload
    elif payload_file is not None:
        # Load payload from JSON file
        query_payload = load_query_payload_from_json(payload_file)
    else:
        # Build payload from individual parameters (backward compatibility)
        if not metric_id or not axes:
            raise ValueError(
                "Either 'payload', 'payload_file', or both 'metric_id' and 'axes' must be provided"
            )
        query_payload = build_vanilla_aggregate_query(
            metric_id=metric_id,
            axes=axes,
            filters=filters,
            time_intervals=time_intervals,
            parameter_values=parameter_values,
            options=options
        )
    
    # Build the API URL (Postman collection pattern)
    # Try both endpoints - Postman may use /v1/aggregate or /v1/data/query/aggregate
    host = config["host"].rstrip('/')
    vanity = config["vanity"]
    
    # Primary endpoint from API reference
    url = f"{host}/v1/data/query/aggregate"
    
    # Prepare headers (Postman collection pattern)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Add API key if provided
    if config.get("apikey"):
        headers["apikey"] = config["apikey"]
    
    # Prepare cookies: ASID token as cookie (Postman collection pattern)
    # Postman shows: Cookie: VisierASIDToken=<your_asid_token>
    # So the cookie value is just the token, not "VisierASIDToken={token}"
    cookies = {
        "VisierASIDToken": asid_token
    }
    
    # Prepare query parameters
    params = {}
    if vanity:
        params["vanity"] = vanity
    
    # Make the request
    response = requests.post(
        url,
        json=query_payload,  # requests will automatically JSON-encode this
        headers=headers,
        cookies=cookies,  # ASID token as cookie (Postman pattern)
        params=params
    )
    
    # Check for errors
    if response.status_code != 200:
        # Try to get error details from response
        try:
            error_data = response.json()
            error_msg = f"API Error {response.status_code}: {error_data}"
        except:
            error_msg = f"API Error {response.status_code}: {response.text}"
        raise requests.HTTPError(f"{error_msg}\nURL: {url}\nPayload: {json.dumps(query_payload, indent=2)}")
    
    response.raise_for_status()
    
    # Parse and return response
    return response.json()


def convert_vanilla_response_to_dataframe(
    response: Dict[str, Any],
    metric_id: Optional[str] = None
) -> 'pd.DataFrame':  # type: ignore
    """
    Convert vanilla API response (CellSetDTO) to pandas DataFrame.
    
    Args:
        response: The API response dictionary (CellSetDTO structure)
        metric_id: Optional metric ID to add as a column. If None, will try to extract from response.
    
    Returns:
        pandas DataFrame with dimension columns and metric value column
    """
    import pandas as pd
    
    # Check if response has error
    if "error" in response:
        error = response["error"]
        error_msg = f"Query failed: {error.get('message', 'Unknown error')}"
        if "errorCode" in error:
            error_msg += f" (Code: {error['errorCode']})"
        raise ValueError(error_msg)
    
    # Extract cells and axes (Postman collection response structure)
    # Response is {'cells': [...], 'axes': [...]} at top level (not wrapped in 'cellSet')
    cells = response.get("cells", [])
    axes = response.get("axes", [])
    
    if not cells:
        return pd.DataFrame()
    
    # Try to extract metric name from response if not provided
    if metric_id is None:
        # Check if there's a Measures axis or source information
        for axis in axes:
            # Look for measure/metric information in axes
            if "measure" in axis or "metric" in axis:
                metric_id = axis.get("measure") or axis.get("metric")
                break
        # Also check response metadata
        if metric_id is None and "source" in response:
            source = response.get("source", {})
            metric_id = source.get("metric") or source.get("measure")
    
    if not axes:
        # No axes - just return metric values
        values = []
        for cell in cells:
            cell_value = cell.get("value")
            if cell_value is None or cell_value == "":
                values.append(None)
            else:
                try:
                    values.append(float(cell_value))
                except (ValueError, TypeError):
                    values.append(None)
        df = pd.DataFrame({"value": values})
        if metric_id:
            df["Measures"] = metric_id
        return df
    
    # Build dimension names from axes
    dimension_names = []
    measures_axis_idx = None
    for i, axis in enumerate(axes):
        # Check if this is a Measures axis (contains metric/measure info)
        if "measure" in axis or "metric" in axis or "measures" in str(axis).lower():
            measures_axis_idx = i
            # Try to extract metric name from this axis
            if metric_id is None:
                metric_id = axis.get("measure") or axis.get("metric")
                # Check positions for measure names
                if "positions" in axis and axis["positions"]:
                    pos = axis["positions"][0]
                    if "path" in pos:
                        path = pos["path"]
                        if isinstance(path, list) and len(path) > 0:
                            metric_id = str(path[-1])
                        else:
                            metric_id = str(path)
                    elif "members" in pos and pos["members"]:
                        metric_id = pos["members"][0].get("name") or pos["members"][0].get("memberId")
            dimension_names.append("Measures")
        elif "dimension" in axis and axis["dimension"]:
            dim_name = axis["dimension"].get("name", f"Dimension_{len(dimension_names)}")
            dimension_names.append(dim_name)
        else:
            dimension_names.append(f"Dimension_{len(dimension_names)}")
    
    # Build position lookup for each axis
    # Positions have 'path' arrays - use the last element or full path
    axis_positions = []
    for axis in axes:
        positions = {}
        if "positions" in axis:
            for i, position in enumerate(axis["positions"]):
                if "path" in position:
                    path = position["path"]
                    if isinstance(path, list) and len(path) > 0:
                        # Use the last element of the path (most specific)
                        position_name = str(path[-1])
                    else:
                        position_name = str(path)
                elif "members" in position and position["members"]:
                    # Fallback: try members if path not available
                    member = position["members"][0]
                    position_name = member.get("name") or member.get("memberId") or f"Position_{i}"
                else:
                    position_name = f"Position_{i}"
                positions[i] = position_name
        axis_positions.append(positions)
    
    # Build DataFrame rows
    rows = []
    for cell in cells:
        row = {}
        
        # Add dimension values from cell coordinates
        # Coordinates are indices into the axes positions
        if "coordinates" in cell:
            coordinates = cell["coordinates"]
            for i, coord_idx in enumerate(coordinates):
                if i < len(axis_positions):
                    dim_name = dimension_names[i] if i < len(dimension_names) else f"Dimension_{i}"
                    pos_map = axis_positions[i]
                    # For Measures axis, use the metric_id if available, otherwise use position name
                    if dim_name == "Measures" and metric_id:
                        row[dim_name] = metric_id
                    else:
                        row[dim_name] = pos_map.get(coord_idx, f"Position_{coord_idx}")
        
        # Add metric value (handle empty strings and None)
        cell_value = cell.get("value")
        if cell_value is None or cell_value == "":
            row["value"] = None
        else:
            try:
                row["value"] = float(cell_value)
            except (ValueError, TypeError):
                row["value"] = None
        
        # Add support if available
        if "support" in cell:
            support_value = cell.get("support")
            if support_value is None or support_value == "":
                row["support"] = None
            else:
                try:
                    row["support"] = int(support_value)
                except (ValueError, TypeError):
                    row["support"] = None
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # If we have a metric_id but no Measures column, add it
    if metric_id and "Measures" not in df.columns:
        df.insert(0, "Measures", metric_id)
    
    return df

