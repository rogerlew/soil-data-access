import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_transport_contract import validate_table, verify


class TransportContractTests(unittest.TestCase):
    def test_authored_shapes(self):
        self.assertTrue(all(r['shape']=='passed' for r in verify()))

    def test_wrong_header_width_or_cell_type_fails(self):
        for body in ('<html>502 Bad Gateway</html>', {}, {'Table':[]}, {'Table':[['wrong']]}, {'Table':[['id','name'],['1']]}, {'Table':[['id','name'],[1,'soil']]}, {'Table':[['id','name'],[True,'soil']]}, {'Table':[['id','name']],'Extra':1}):
            with self.subTest(body=body),self.assertRaises(ValueError):
                validate_table(body,['id','name'])

    def test_null_empty_and_exact_large_id_survive_wire_validation(self):
        rows=[['9007199254740993',None],['1',''],['2','  text  ']]
        self.assertEqual(validate_table({'Table':[['id','name']]+rows},['id','name']),rows)


if __name__=='__main__':unittest.main()
