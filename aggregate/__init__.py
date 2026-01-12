"""
Visier Aggregate Query Module

This module provides a simple, RESTful API-based interface for querying
aggregate metrics from Visier without SDK dependencies.

Quick Start:
    from aggregate.aggregate_query_vanilla import (
        execute_vanilla_aggregate_query,
        convert_vanilla_response_to_dataframe,
        create_dimension_axis
    )
    
    axes = [create_dimension_axis("Function")]
    response = execute_vanilla_aggregate_query(metric_id="employeeCount", axes=axes)
    df = convert_vanilla_response_to_dataframe(response, metric_id="employeeCount")
"""

__version__ = "1.0.0"
