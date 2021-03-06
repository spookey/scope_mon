from fnmatch import fnmatch
from os import listdir, path
from string import ascii_lowercase, digits

from pygal import DateTimeLine, Treemap, Pie

from lib.common import DATADIR, ts_dt
from lib.files import readjson


class PlotNode:
    def __init__(self, data):
        self.hostname = data['hostname']
        self.name = ''.join(
            c for c in self.hostname.lower() if
            c in (ascii_lowercase + digits + '_' + '-')
        )
        self.data = {}

        for ts in sorted(data['log']):
            for field in sorted(data['log'][ts]):
                self.data[field] = self.data.get(field, [])
                self.data[field].append((
                    ts_dt(float(ts)),
                    data['log'][ts][field]
                ))

    def _plot(self, x_title):
        plot = DateTimeLine(
            legend_at_bottom=True,
            title=self.hostname,
            x_label_rotation=35,
            x_value_formatter=lambda dt: dt.strftime('%Y.%m.%d %H:%M:%S')
        )
        plot.x_title = x_title
        return plot

    def clients(self):
        plot = self._plot('Clients')
        plot.add('WiFi', self.data['clients_wifi'])
        plot.add('Total', self.data['clients_total'])
        return plot

    def traffic(self):
        plot = self._plot('Traffic')
        plot.add('RX', self.data['traffic_rx'])
        plot.add('TX', self.data['traffic_tx'])
        return plot

    def traffic_full(self):
        plot = self.traffic()
        plot.x_title = 'Traffic (full)'
        plot.add('Forward', self.data['traffic_forward'])
        plot.add('Management RX', self.data['traffic_mgmt_rx'])
        plot.add('Management TX', self.data['traffic_mgmt_tx'])
        return plot

    def system(self):
        plot = self._plot('System')
        plot.add('Load', self.data['load_avg'])
        return plot


def save(name, graph, field):
    graph.render_to_file(
        path.join(DATADIR, '{}_{}.svg'.format(name, field))
    )


def _load():
    sdata = {
        'log': {},
        'hostname': 'Summary'
    }

    for jf in listdir(DATADIR):
        if fnmatch(jf, '*.json'):
            data = readjson(path.join(DATADIR, jf))
            yield PlotNode(data)

            for ts in data['log']:

                sdata['log'][ts] = sdata['log'].get(ts, {})
                for field in data['log'][ts]:
                    dt = data['log'][ts][field]
                    sdata['log'][ts][field] = sdata['log'][ts].get(field, 0)
                    if dt is not None:
                        sdata['log'][ts][field] += dt

    sum_node = PlotNode(sdata)
    save('_sum', sum_node.clients(), 'clients')
    save('_sum', sum_node.traffic(), 'traffic')
    save('_sum', sum_node.traffic_full(), 'traffic_full')


def plot():
    def _cmp(comp, node, field):
        comp.add(node.hostname, [d[-1] for d in node.data[field]])
        return comp

    tree_clients, pie_clients = Treemap(), Pie()
    tree_traffic_rx, pie_traffic_rx = Treemap(), Pie()
    tree_traffic_tx, pie_traffic_tx = Treemap(), Pie()

    for node in _load():
        save(node.name, node.clients(), 'clients')
        save(node.name, node.system(), 'system')
        save(node.name, node.traffic(), 'traffic')
        save(node.name, node.traffic_full(), 'traffic_full')

        save('_map', _cmp(tree_clients, node, 'clients_total'), 'clients')
        save('_pie', _cmp(pie_clients, node, 'clients_total'), 'clients')

        save('_map', _cmp(tree_traffic_rx, node, 'traffic_rx'), 'traffic_rx')
        save('_pie', _cmp(pie_traffic_rx, node, 'traffic_rx'), 'traffic_rx')

        save('_map', _cmp(tree_traffic_tx, node, 'traffic_tx'), 'traffic_tx')
        save('_pie', _cmp(pie_traffic_tx, node, 'traffic_tx'), 'traffic_tx')
