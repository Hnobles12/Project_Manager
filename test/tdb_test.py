import tinydb as tdb


class Db:

    def __init__(self, db_file):
        self.db = tdb.TinyDB(db_file)
        self.Pkg = tdb.Query()

    def get_pkg(self, pkg_name):
        pkg_data = self.db.search(self.Pkg.name == pkg_name)
        # print(pkg_data)
        return pkg_data

    def get_pkg_names(self) -> list[str]:
        return [d.get('name') for d in self.db.all()]

    def get_CRs(self) -> list[str]:
        CRs = [d.get('CR') for d in self.db.all()]
        return [*set(CRs)]

    def get_pkg_names_by_CR(self, CR):
        return [d.get('name') for d in self.db.search(self.Pkg.CR == CR)]

    def insert_pkg(self, pkg: dict):
        self.db.insert(pkg)

    def update_pkg(self, pkg_name, pkg_dict):

        for pkg in self.get_pkg(pkg_name):
            # pkg.update(pkg_dict)
            self.db.update(pkg_dict, self.Pkg.name == pkg_name)


db = Db('test.json')
# db.db.purge()
db.db.insert({'name': '2WBH1', 'CR': 'CR-036371', 'data': "test data1."})
db.db.insert({'name': '2WBH2', 'CR': 'CR-036395', 'data': "test data2."})
db.db.insert({'name': '2WBH3', 'CR': 'CR-036380', 'data': "test data3."})

data = db.get_pkg('2WBH1')
print(data)
# print(db.get_pkg_names())
# print(db.get_CRs())
# print(db.get_pkg_names_by_CR('CR-036371'))
db.update_pkg('2WBH1', {'CR': 'CR-012345', 'notes': 'Hello\nWorld.'})
print(db.get_pkg('2WBH1'))
