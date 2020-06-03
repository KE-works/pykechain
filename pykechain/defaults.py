"""All pykechain configuration constants will be listed here."""
#
# Configuration of async download of activity pdf exports
#
ASYNC_REFRESH_INTERVAL = 2  # seconds
ASYNC_TIMEOUT_LIMIT = 100  # seconds

#
# Configuration of the retry options for the client requests based on `urlib3.utils.Retry`.
#

# How many connection-related errors to retry on.
# These are errors raised before the request is sent to the remote server,
# which we assume has not triggered the server to process the request.
RETRY_ON_CONNECTION_ERRORS = 3  # times

# How many times to retry on read errors.
# These errors are raised after the request was sent to the server, so the request may have side-effects.
RETRY_ON_READ_ERRORS = 2

# How many redirects to perform. Limit this to avoid infinite redirect loops.
# A redirect is a HTTP response with a status code 301, 302, 303, 307 or 30
RETRY_ON_REDIRECT_ERRORS = 1

# Total number of retries to allow. Takes precedence over other counts
RETRY_TOTAL = 10

# A backoff factor to apply between attempts after the second try (most errors are resolved
# immediately by a second try without a delay). urllib3 will sleep for:
# {backoff factor} * (2 ** ({number of total retries} - 1)) seconds.
# If the backoff_factor is 0.1, then sleep() will sleep for [0.0s, 0.2s, 0.4s, …] between retries.
RETRY_BACKOFF_FACTOR = 0.8

#
# API Paths and API Extra Parameters
#
API_PATH = {
    'scopes': 'api/scopes.json',
    'scope': 'api/scopes/{scope_id}.json',
    'activities': 'api/activities.json',
    'activity': 'api/activities/{activity_id}.json',
    'activity_export': 'api/activities/{activity_id}/export',
    'activity_move': 'api/activities/{activity_id}/move_activity',
    'activities_bulk_update': 'api/activities/bulk_update',
    'parts': 'api/parts.json',
    'part': 'api/parts/{part_id}.json',
    'properties': 'api/properties.json',
    'property': 'api/properties/{property_id}.json',
    'property_upload': 'api/properties/{property_id}/upload',
    'property_download': 'api/properties/{property_id}/download',
    'widgets_config': 'api/widget_config.json',
    'widget_config': 'api/widget_config/{widget_config_id}.json',
    'services': 'api/services.json',
    'service': 'api/services/{service_id}.json',
    'service_execute': 'api/services/{service_id}/execute',
    'service_upload': 'api/services/{service_id}/upload',
    'service_download': 'api/services/{service_id}/download',
    'service_executions': 'api/service_executions.json',
    'service_execution': 'api/service_executions/{service_execution_id}.json',
    'service_execution_terminate': 'api/service_executions/{service_execution_id}/terminate',
    'service_execution_notebook_url': 'api/service_executions/{service_execution_id}/notebook_url',
    'service_execution_log': 'api/service_executions/{service_execution_id}/log',
    'users': 'api/users.json',
    'user_current': 'api/users/get_current_user',
    'teams': 'api/teams.json',
    'team': 'api/teams/{team_id}.json',
    'team_add_members': 'api/teams/{team_id}/add_members',
    'team_remove_members': 'api/teams/{team_id}/remove_members',
    'versions': 'api/versions.json',
    'associations': 'api/associations.json',

    # PIM3
    'scope2': 'api/v3/scopes/{scope_id}.json',
    'scope2_add_member': 'api/v3/scopes/{scope_id}/add_member',
    'scope2_remove_member': 'api/v3/scopes/{scope_id}/remove_member',
    'scope2_add_manager': 'api/v3/scopes/{scope_id}/add_manager',
    'scope2_remove_manager': 'api/v3/scopes/{scope_id}/remove_manager',
    'scope2_add_leadmember': 'api/v3/scopes/{scope_id}/add_leadmember',
    'scope2_remove_leadmember': 'api/v3/scopes/{scope_id}/remove_leadmember',
    'scopes2': 'api/v3/scopes.json',
    'scopes2_clone': 'api/v3/scopes/clone',
    'parts2': 'api/v3/parts.json',
    'parts2_new_instance': 'api/v3/parts/new_instance',
    'parts2_create_child_model': 'api/v3/parts/create_child_model',
    'parts2_create_proxy_model': 'api/v3/parts/create_proxy_model',
    'parts2_clone_model': 'api/v3/parts/clone_model',
    'parts2_clone_instance': 'api/v3/parts/clone_instance',
    'parts2_export': 'api/v3/parts/export',
    'part2': 'api/v3/parts/{part_id}.json',
    'properties2': 'api/v3/properties.json',
    'properties2_bulk_update': 'api/v3/properties/bulk_update',
    'properties2_create_model': 'api/v3/properties/create_model',
    'property2': 'api/v3/properties/{property_id}.json',
    'property2_upload': 'api/v3/properties/{property_id}/upload',
    'property2_download': 'api/v3/properties/{property_id}/download',
    'widgets': 'api/widgets.json',
    'widget': 'api/widgets/{widget_id}.json',
    'widget_clear_associations': 'api/widgets/{widget_id}/clear_associations.json',
    'widget_remove_associations': 'api/widgets/{widget_id}/remove_associations.json',
    'widgets_update_associations': 'api/widgets/bulk_update_associations.json',
    'widget_update_associations': 'api/widgets/{widget_id}/update_associations.json',
    'widgets_set_associations': 'api/widgets/bulk_set_associations.json',
    'widget_set_associations': 'api/widgets/{widget_id}/set_associations.json',
    'widgets_bulk_create': 'api/widgets/bulk_create',
    'widgets_bulk_delete': 'api/widgets/bulk_delete',
    'widgets_bulk_update': 'api/widgets/bulk_update',
    'widgets_schemas': 'api/widgets/schemas',
    'notifications': 'api/v3/notifications.json',
    'notification': 'api/v3/notifications/{notification_id}.json',
    'notification_share_activity_link': 'api/v3/notifications/share_activity_link',
    'notification_share_activity_pdf': 'api/v3/notifications/share_activity_pdf',
    'banners': 'api/v3/banners.json',
    'banner': 'api/v3/banners/{banner_id}.json',
    'banner_active': 'api/v3/banners/active.json',
}
API_QUERY_PARAM_ALL_FIELDS = {'fields': '__all__'}
API_EXTRA_PARAMS = {
    'activity': {'fields': ",".join(
        ['id', 'name', 'ref', 'description', 'created_at', 'updated_at', 'activity_type', 'classification', 'tags',
         'progress', 'assignees_ids', 'start_date', 'due_date', 'status', 'parent_id', 'scope_id', 'customization',
         'activity_options'])},
    'activities': {'fields': ",".join(
        ['id', 'name', 'ref', 'description', 'created_at', 'updated_at', 'activity_type', 'classification', 'tags',
         'progress', 'assignees_ids', 'start_date', 'due_date', 'status', 'parent_id', 'scope_id', 'customization',
         'activity_options'])},
    'banner': {'fields': ",".join(
        ['id', 'text', 'icon', 'is_active', 'active_from', 'active_until', 'url', 'created_at', 'updated_at'])},
    'banners': {'fields': ",".join(
        ['id', 'text', 'icon', 'is_active', 'active_from', 'active_until', 'url', 'created_at', 'updated_at'])},
    'scope2': {'fields': ",".join(
        ['id', 'name', 'ref', 'text', 'created_at', 'updated_at', 'start_date', 'due_date', 'status', 'category',
         'progress', 'members', 'team', 'tags', 'scope_options', 'team_id_name', 'workflow_root_id'])},
    'scopes2': {'fields': ",".join(
        ['id', 'name', 'ref', 'text', 'created_at', 'updated_at', 'start_date', 'due_date', 'status', 'category',
         'progress', 'members', 'team', 'tags', 'scope_options', 'team_id_name', 'workflow_root_id'])},
    'part2': {'fields': ",".join(
        ['id', 'name', 'ref', 'description', 'created_at', 'updated_at', 'properties', 'category', 'classification',
         'parent_id', 'multiplicity', 'value_options', 'property_type', 'value', 'output', 'order',
         'part_id', 'scope_id', 'model_id', 'proxy_source_id_name', 'unit'])},
    'parts2': {'fields': ",".join(
        ['id', 'name', 'ref', 'description', 'created_at', 'updated_at', 'properties', 'category', 'classification',
         'parent_id', 'multiplicity', 'value_options', 'property_type', 'value', 'output', 'order',
         'part_id', 'scope_id', 'model_id', 'proxy_source_id_name', 'unit'])},
    'properties2': {'fields': ",".join(
        ['id', 'name', 'ref', 'created_at', 'updated_at', 'model_id', 'part_id', 'order', 'scope_id', 'category',
         'property_type', 'value', 'value_options', 'output', 'description', 'unit'])},
    'property2': {'fields': ",".join(
        ['id', 'name', 'ref', 'created_at', 'updated_at', 'model_id', 'part_id', 'order', 'scope_id', 'category',
         'property_type', 'value', 'value_options', 'output', 'description', 'unit'])},
    'service': {'fields': ",".join(
        ['id', 'name', 'ref', 'created_at', 'updated_at', 'script_version', 'script_type', 'script_file_name',
         'description', 'env_version', 'scope', 'run_as', 'trusted', 'verified_on', 'verification_results'])},
    'services': {'fields': ",".join(
        ['id', 'name', 'ref', 'created_at', 'updated_at', 'script_version', 'script_type', 'script_file_name',
         'description', 'env_version', 'scope', 'run_as', 'trusted', 'verified_on', 'verification_results'])},
    'widgets': {'fields': ",".join(
        ['id', 'name', 'ref', 'created_at', 'updated_at', 'title', 'widget_type', 'meta', 'order', 'activity_id',
         'parent_id', 'progress', 'has_subwidgets', 'scope_id'])},
    'widget': {'fields': ",".join(
        ['id', 'name', 'ref', 'created_at', 'updated_at', 'title', 'widget_type', 'meta', 'order', 'activity_id',
         'parent_id', 'progress', 'has_subwidgets', 'scope_id'])},
    'notifications': {'fields': ",".join(
        ['id', 'subject', 'status', 'message', 'team', 'created_at', 'options', 'updated_at'])},
    'notification': {'fields': ",".join(
        ['id', 'subject', 'status', 'message', 'team', 'created_at', 'options', 'updated_at'])},
}
