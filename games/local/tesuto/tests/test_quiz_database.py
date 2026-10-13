"""実際のxlsxのコピーを編集し、出題・再読込・入力エラーを確認します。"""
from pathlib import Path
import random
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quiz_database import DEFAULT_PATH, QuestionDatabase
from web_game import Store, WebGame

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def edit_copy(path, edits, sheet=1):
    """テスト用コピーだけを変更。Excelアプリや追加の作成ライブラリは不要。"""
    source = path if path.exists() else DEFAULT_PATH
    with ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    name = f'xl/worksheets/sheet{sheet}.xml'
    tree = ET.fromstring(files[name])
    data = tree.find(NS+'sheetData')
    highest = max(int(row.get('r')) for row in data)
    for address, value in edits.items():
        row_number = int(''.join(c for c in address if c.isdigit()))
        row = next((r for r in data if int(r.get('r')) == row_number), None)
        if row is None:
            row = ET.SubElement(data, NS+'row', r=str(row_number))
        cell = next((c for c in row if c.get('r') == address), None)
        if cell is None:
            cell = ET.SubElement(row, NS+'c', r=address)
        for child in list(cell):
            cell.remove(child)
        cell.attrib.pop('t', None)
        if isinstance(value, str):
            if value.startswith('='):
                ET.SubElement(cell, NS+'f').text=value[1:]
            else:
                cell.set('t','inlineStr')
                ET.SubElement(ET.SubElement(cell,NS+'is'),NS+'t').text=value
        elif value is not None:
            ET.SubElement(cell,NS+'v').text=str(value)
        highest=max(highest,row_number)
    dimension = tree.find(NS+'dimension')
    if dimension is not None:
        dimension.set('ref',f'A1:K{highest}')
    files[name]=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w') as archive:
        for name,content in files.items():
            archive.writestr(name,content)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.path=self.folder/'questions.xlsx'

    def test_edit_add_disable_and_preserve_text_answers(self):
        edit_copy(self.path,{'B2':'無効','D3':'編集した問題','E3':'001', 'A300':'QA-ADD','B300':'有効','C300':3,'D300':'追加問題','E300':'正解','F300':'不正解'})
        database=QuestionDatabase(self.path)
        self.assertFalse(any(q.id=='L02-001' for q in database.questions[2]))
        self.assertTrue(any(q.text=='編集した問題' and q.answer=='001' for q in database.questions[2]))
        self.assertTrue(any(q.id=='QA-ADD' for q in database.questions[3]))
        for level in range(2,11):
            for question in database.questions[level]:
                self.assertTrue(question.wrong)
                self.assertNotIn(question.answer,question.wrong)

    def test_invalid_headers_ids_answers_levels_and_formula(self):
        cases=[({'A1':'改名'},'1行目'),({'A3':'L02-001'},'3行目'),({'E2':None},'2行目'),({'F2':'H'},'2行目'),({'C2':11},'2行目'),({'E2':'=1+1'},'数式'),({'B2':'yes'},'有効')]
        for edits,message in cases:
            self.path.unlink(missing_ok=True)
            edit_copy(self.path,edits)
            with self.assertRaisesRegex(ValueError,message):
                QuestionDatabase(self.path)

    def test_empty_fixed_level_is_reported(self):
        database=QuestionDatabase()
        edits={f'B{index+2}':'無効' for index,question in enumerate([q for level in range(2,11) for q in database.questions[level]]) if question.level==3}
        edit_copy(self.path,edits)
        with self.assertRaisesRegex(ValueError,'Lv.3に有効な問題'):
            QuestionDatabase(self.path)

    def test_math_bounds_and_level_titles_are_read_from_excel(self):
        edit_copy(self.path,{'B2':'Lv.1: 編集した計算','E2':2,'F2':2,'G2':3,'H2':3},sheet=2)
        database=QuestionDatabase(self.path)
        self.assertEqual(database.level_infos[0][0],'Lv.1: 編集した計算')
        rng=random.Random(4)
        answers={database.generate(1,rng)[1] for _ in range(100)}
        self.assertEqual(answers,{'4','0','9'})
        edit_copy(self.path,{'E2':5,'F2':2},sheet=2)
        with self.assertRaisesRegex(ValueError,'最小値'):
            QuestionDatabase(self.path)

    def test_next_start_reloads_but_running_game_keeps_its_database(self):
        edit_copy(self.path,{'D2':'変更前'})
        store=Store(self.folder/'saved',self.folder/'original')
        game=WebGame(store,quiz_path=self.path)
        game.start({'level':2})
        edit_copy(self.path,{'D2':'変更後'})
        self.assertEqual(game.database.questions[2][0].text,'変更前')
        game.stop();game.start({'level':2})
        self.assertEqual(game.database.questions[2][0].text,'変更後')
        game.stop()
        edit_copy(self.path,{'E2':None})
        with self.assertRaises(ValueError):
            game.start({'level':2})
        self.assertEqual(game.phase,'menu')

    def test_missing_file_and_workbook_structure(self):
        with self.assertRaisesRegex(ValueError,'開けません'):
            QuestionDatabase(self.path)
        database=QuestionDatabase()
        self.assertEqual(len(database.level_infos),10)
        for level in range(1,11):
            question,answer,wrong=database.generate(level)
            self.assertTrue(question and answer and wrong)


if __name__=='__main__':
    unittest.main()
