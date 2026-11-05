import ast
import datetime
from pathlib import Path
import unittest

# Load the calculation functions without requiring NVDA or wxPython.
source = Path(__file__).resolve().parents[1] / "addon/globalPlugins/calendario_simples_BR.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
names = {"get_feriados_moveis", "calcular_intervalo", "buscar_data_por_quantidade"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
nodes += [node for node in tree.body if isinstance(node, ast.Assign) and any(
    isinstance(target, ast.Name) and target.id == "FERIADOS_FIXOS" for target in node.targets
)]
namespace = {"datetime": datetime}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)
calcular = namespace["calcular_intervalo"]
buscar = namespace["buscar_data_por_quantidade"]
D = datetime.date


class IntervaloTest(unittest.TestCase):
    def test_intervalo_inclusivo_e_final_de_semana(self):
        resultado = calcular(D(2026, 11, 5), D(2026, 12, 31))
        self.assertEqual((resultado["total"], resultado["uteis"], resultado["fim_semana"]), (57, 39, 16))
        self.assertEqual(len(resultado["feriados"]), 3)
        self.assertEqual(resultado["feriados_em_dias_uteis"], 2)
        self.assertEqual(resultado["dias_semana"], [8, 8, 8, 9, 8, 8, 8])

    def test_feriados_moveis(self):
        for data in (D(2026, 2, 17), D(2026, 4, 3), D(2026, 6, 4)):
            with self.subTest(data=data):
                resultado = calcular(data, data)
                self.assertEqual(resultado["uteis"], 0)
                self.assertEqual(len(resultado["feriados"]), 1)

    def test_consciencia_negra_antes_e_depois_da_lei(self):
        self.assertFalse(calcular(D(2023, 11, 20), D(2023, 11, 20))["feriados"])
        self.assertEqual(calcular(D(2024, 11, 20), D(2024, 11, 20))["uteis"], 0)

    def test_bissexto_e_passagem_de_ano(self):
        self.assertEqual(calcular(D(2024, 2, 28), D(2024, 3, 1))["total"], 3)
        resultado = calcular(D(2025, 12, 31), D(2026, 1, 2))
        self.assertEqual((resultado["total"], resultado["uteis"]), (3, 2))

    def test_ajuste_das_contagens(self):
        inicio = D(2026, 11, 5)  # quinta-feira
        self.assertEqual(buscar(inicio, D(2026, 11, 6), "uteis", 3), D(2026, 11, 9))
        self.assertEqual(buscar(inicio, D(2026, 11, 9), "uteis", 2), D(2026, 11, 8))
        self.assertEqual(buscar(inicio, D(2026, 11, 6), "fim_semana", 1), D(2026, 11, 7))
        self.assertEqual(buscar(inicio, D(2026, 11, 9), "fim_semana", 0), D(2026, 11, 6))
        self.assertEqual(buscar(inicio, D(2026, 11, 9), "total", 1), inicio)
        with self.assertRaises(ValueError):
            buscar(inicio, inicio, "total", 0)

    def test_contagem_retroativa(self):
        inicio, fim = D(2026, 11, 9), D(2026, 11, 5)
        self.assertEqual(calcular(inicio, fim), calcular(fim, inicio))
        self.assertEqual(buscar(inicio, fim, "total", 6, -1), D(2026, 11, 4))
        self.assertEqual(buscar(inicio, fim, "total", 2, -1), D(2026, 11, 8))
        self.assertEqual(buscar(inicio, fim, "uteis", 2, -1), D(2026, 11, 6))
        self.assertEqual(buscar(inicio, D(2026, 11, 6), "uteis", 3, -1), D(2026, 11, 5))
        self.assertEqual(buscar(inicio, inicio, "total", 2, -1), D(2026, 11, 8))
        self.assertEqual(buscar(inicio, fim, "fim_semana", 1, -1), D(2026, 11, 8))
        self.assertEqual(buscar(inicio, fim, "fim_semana", 0, -1), inicio)
        with self.assertRaises(ValueError):
            buscar(inicio, D(2026, 11, 10), "total", 2, -1)

    def test_intervalo_invalido(self):
        for inicio, fim in ((D(1999, 1, 1), D(2000, 1, 1)), (D(2099, 1, 1), D(2100, 1, 1)), (D(2100, 1, 1), D(2099, 1, 1))):
            with self.subTest(inicio=inicio, fim=fim), self.assertRaises(ValueError):
                calcular(inicio, fim)


if __name__ == "__main__":
    unittest.main()
