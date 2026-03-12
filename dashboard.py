from grafanalib.core import Dashboard, Graph, Row, Target, GridPos, OPS_FORMAT
import json

dashboard = Dashboard(
    title="System Information Dashboard",
    description="Dashboard for hardware and OS information",
    tags=["system", "hardware", "os"],
    timezone="browser",
    panels=[
        Graph(
            title="CPU Info",
            dataSource="System Info API",
            targets=[
                Target(
                    expr='',
                    queryType="json",
                    target='',
                    refId='A',
                    datasource="System Info API",
                    # Для Infinity плагина нужны специальные параметры
                    # Это пример - может отличаться в зависимости от версии
                ),
            ],
            gridPos=GridPos(h=8, w=12, x=0, y=0),
        ),
        Graph(
            title="Memory Info",
            dataSource="System Info API",
            gridPos=GridPos(h=8, w=12, x=12, y=0),
        ),
    ],
).auto_panel_ids()

# Сохраняем в JSON
with open('dashboard.json', 'w') as f:
    json.dump(dashboard.to_json_data(), f, indent=2)