from pykechain.enums import ComponentXType
from pykechain.exceptions import InspectorComponentError
from pykechain.models import Base
from pykechain.models.inspector_base import InspectorComponent


class HtmlPanel(InspectorComponent):
    """HTML Panel Component for the inspector."""

    def __init__(self, json=None, html=None, title=None, **kwargs):
        """
        Instantiate a html panel.

        Provide either json or html

        :param json: provide a valid json (optional if not part)
        :param html: provide a html string (nicely escaped please) (optional if not json)
        :param title: provide a title (optional)
        :param kwargs: optional extra kwargs
        """
        if not json and html:
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.PANEL,
                title=title,
                html=html
            ))
        elif json:
            super(self.__class__, self).__init__(json=json)
        else:
            raise InspectorComponentError("Either provide json or html")


class PropertyGrid(InspectorComponent):
    """PropertyGrid component."""

    def __init__(self, json=None, part=None, title=None, **kwargs):
        """
        Instantiate a PropertyGrid.

        Provide either json or (parent and model or activity)

        :param json: provide a valid json (optional if not part)
        :param part: provide a part id (or pykechain Part) (optional if json)
        :param title: provide a title for the propertygrid (optional)
        :param kwargs: Optional Extras
        """
        if not json and part:
            if isinstance(part, Base):
                part = part.id
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.PROPERTYGRID,
                filter=dict(part=part)
            ))
        elif json and not part:
            super(self.__class__, self).__init__(json=json)
        else:
            raise InspectorComponentError("Either provide json or (parent and model)")

        if title:
            self._json_data['title'] = title
            self._json_data['viewModel'] = {'data': {'style': {'displayPartTitle': True}}}


class SuperGrid(InspectorComponent):
    """The SuperGrid component."""

    def __init__(self, json=None, parent=None, model=None, activity_id=None, title=None, **kwargs):
        """
        Instantiate a SuperGrid.

        Provide either json or (parent and model or activity)

        in kwargs you may: "newInstance" in kwargs or "edit" in kwargs or "delete" in kwargs or "export" in kwargs

        :param json: provide a valid SuperGrid json (optional if not parent & model)
        :param parent: provide a parent id (or pykechain Part) (optional if json)
        :param model: provide a model id (or pykechain Part) (optional if json)
        :param activity_id: provide a acitivity id (or pykechain Activity) (optional)
        :param title: adding title to the component (optional)
        :param newInstance: show this button (default True)
        :param delete: show this button (default True)
        :param edit: show this button (default True)
        :param export: show this button (default True)
        :param kwargs: Optional extra kwargs.
        """
        if not json and parent and model:
            if isinstance(parent, Base):
                parent = parent.id
            if isinstance(model, Base):
                model = model.id
            if isinstance(activity_id, Base):
                activity_id = activity_id.id
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.SUPERGRID,
                title=title,
                filter=dict(
                    parent=parent,
                    model=model,
                    activity_id=activity_id),
                viewModel=dict(
                    data=dict(
                        actions=dict(
                            newInstance=kwargs.get("newInstance", True),
                            edit=kwargs.get("edit", True),
                            delete=kwargs.get("delete", True),
                            export=kwargs.get("export", True)
                        )
                    )
                )
            ))
        elif json and not parent and not model:
            super(self.__class__, self).__init__(json=json)
        else:
            raise InspectorComponentError("Either provide json or (parent and model)")

    def get(self, item):
        """Get an item from the filter subdict.

        :param item: item to retrieve. eg. model, parent, activity_id
        :return: uuid (as string)
        """
        return self._json_data['filter'].get(item, None)

    def set(self, key, value):
        """Set an item to a value in the filter subdictionary.

        :param key: string to set e.g model, parent, activity_id
        :param value: UUID as string or an pykechain object (will retrieve the id from that)
        :return: None
        """
        if isinstance(value, Base):
            value = value.id
        self._json_data['filter'][key] = value


class FilteredGrid(InspectorComponent):
    """Filtered and Paginated Grid component for a task customization in KE-chain 2.

    Example json for the configuration::

        {
          "xtype": "filteredGrid",
          "parentInstanceId": "02a2a979-2e3-b32212a0ca83",
          "partModelId": "bfe90c01-7d8c-4ab97eac4ebf",
          "collapseFilters": false,
          "pageSize": 25,
          "flex": 0,
          "height": 600,
          "grid": {
            "xtype": "paginatedSuperGrid",
            "viewModel": {
              "data": {
                "actions": {
                  "delete": true,
                  "newInstance": true,
                  "edit": true,
                  "export": true
                }
              }
            }
          }
        }

    """

    def __init__(self, json=None, parent=None, model=None, title=None, **kwargs):
        """
        Instantiate a FilteredGrid Component.

        :param json: provide a valid SuperGrid json (optional if not parent & model)
        :param parent: provide a parent id (or pykechain Part) (optional if json)
        :param model: provide a model id (or pykechain Part) (optional if json)
        :param title: provide a title
        :param collapsefilters: boolean, True to collapse the Filterpane on view (default False)
        :param pagesize: integer to set the pagesize of the page (default 25)
        :param flex: integer to set drawing behaviour (defaults to 0)
        :param height: integer for the hieght of the grid (defaults to 600)
        :param newInstance: show this button (default True)
        :param delete: show this button (default True)
        :param edit: show this button (default True)
        :param export: show this button (default True)
        :param kwargs:
        """
        if not json and parent and model:
            if isinstance(parent, Base):
                parent = parent.id
            if isinstance(model, Base):
                model = model.id
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.FILTEREDGRID,
                parentInstanceId=parent,
                partModelId=model,
                title=title,
                collapseFilters=kwargs.get('collapsefilters', False),
                pageSize=kwargs.get('pagesize', 25),
                flex=kwargs.get('flex', 0),
                height=kwargs.get('height', 600),
                grid=dict(
                    xtype=ComponentXType.PAGINATEDSUPERGRID,
                    viewModel=dict(
                        data=dict(
                            actions=dict(
                                newInstance=kwargs.get('newInstance', True),
                                delete=kwargs.get('delete', True),
                                edit=kwargs.get('edit', True),
                                export=kwargs.get('export', True)
                            )
                        )
                    )
                )
            ))
        elif json and not parent and not model:
            super(self.__class__, self).__init__(json=json)
        else:
            raise InspectorComponentError("Either provide json or (parent and model)")


class PaginatedGrid(InspectorComponent):
    """
    Paginated Grid component for a task customization in KE-chain 2.

    Example JSON defenition::

        {
            "components": [{
                "xtype": "paginatedSuperGrid",
                "filter": {
                    "model": "365e3e6f-38ab-491d-86d6-4dfe51f95804", "parent": "b7658eed-4fab-4c4d-bbed-e68996e89b13"
                }
            }, {
                "xtype": "superGrid",
                "filter": {
                    "model": "365e3e6f-38ab-491d-86d6-4dfe51f95804",
                    "parent": "b7658eed-4fab-4c4d-bbed-e68996e89b13",
                    "limit": 5
                },
                "viewModel": {
                    "data": {
                        "actions": {
                            "edit": false,
                            "newInstance": false,
                            "delete": true
                        }
                    }
                }
            }]
        }

    """

    def __init__(self, json=None, model=None, parent=None, title=None, **kwargs):
        """
        Instantiate the PaginatedGrid component.

        :param json: provide a valid SuperGrid json (optional if not parent & model)
        :param parent: provide a parent id (or pykechain Part) (optional if json)
        :param model: provide a model id (or pykechain Part) (optional if json)
        :param title: provide a title
        :param pagesize: integer to set the pagesize of the page (default 25)
        :param flex: integer to set drawing behaviour (defaults to 0)
        :param height: integer for the hieght of the grid (defaults to 600)
        :param newInstance: show this button (default True)
        :param delete: show this button (default True)
        :param edit: show this button (default True)
        :param export: show this button (default True)
        :param kwargs:
        """
        if not json and parent and model:
            if isinstance(parent, Base):
                parent = parent.id
            if isinstance(model, Base):
                model = model.id
            super(self.__class__, self).__init__(json=dict(
                xtype=ComponentXType.PAGINATEDSUPERGRID,
                filter=dict(
                    model=model,
                    parent=parent
                ),
                title=title,
                pageSize=kwargs.get('pagesize', 25),
                flex=kwargs.get('flex', 0),
                height=kwargs.get('height', 600),
                viewModel=dict(
                    data=dict(
                        actions=dict(
                            newInstance=kwargs.get('newInstance', True),
                            delete=kwargs.get('delete', True),
                            edit=kwargs.get('edit', True),
                            export=kwargs.get('export', True)
                        )
                    )
                )
            ))
        elif json and not parent and not model:
            super(self.__class__, self).__init__(json=json)
        else:
            raise InspectorComponentError("Either provide json or (parent and model)")
