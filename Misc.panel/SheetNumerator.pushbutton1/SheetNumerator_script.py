﻿# -*- coding: utf-8 -*-
""""""
__title__ = 'Нумеровать\nлисты'
__author__ = 'SG'

import clr
clr.AddReference('System.Core')
from System.Collections.Generic import *
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, TransactionGroup, BuiltInParameter, ElementId

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

sheets = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Sheets).ToElements()
sheets = [i for i in sheets \
    if 1 \
    and i.LookupParameter('Имя листа').AsString() != 'Начальный вид']

lst = []
for i in sheets:
	sublist = ['' for s in '012345']
	sublist[0] = i
	sublist[1] = i.LookupParameter('Номер листа').AsString()
	if '-' in sublist[1]:
		sublist[1] = sublist[1][:sublist[1].find('-')]
	for index, pos in enumerate(sublist[1]):
		if pos.isdigit():
			digit = index
			break
	sublist[2] = sublist[1][:digit] # Текстовая часть
	sublist[3] = sublist[1][digit:] # Непосредственно номер
	lst.append(sublist)

def myint(s):
	if s.find(',') == -1 and s.find('.') == -1:
		return int(s)
	else:
		if s.find(',') >= 0:
			return int(s[:s.find(',')])
		else:
			return int(s[:s.find('.')])

lst.sort(key = lambda x: myint(x[3]))
lst.sort(key = lambda x: x[2])

for index, pos in enumerate(lst):
	if index == 0: # Первый раз просто берём номер
		pos[4] = pos[3]
	else:
		prev = lst[index-1][4]
		if '.' in prev: # Если предыдущий с индексом
			prev = int(prev[:prev.find('.')]) # Берём часть до индекса
			if '.' in pos[3]: # Если и в предыдущем и в текущем есть индекс
				current = prev # То не прибавляем единицу
			else:
				current = prev + 1 # Иначе - прибавляем
		else: # Если же предыдущий без индекса
			try:
				prev = int(prev)
			except:
				break
			current = prev + 1 # То прибавляем единицу
		if pos[2] != lst[index-1][2]:
			current = pos[3][:pos[3].find('.')] if pos[3][:pos[3].find('.')] else pos[3]
		if '.' in pos[3]:
			pos[4] = '{}.{}'.format(current, pos[3][pos[3].find('.')+1:])
		else:
			pos[4] = '{}'.format(current)

els = []
for i in lst:
	els = FilteredElementCollector(doc, i[0].Id)
	for e in els:
		if doc.GetElement(e.GetTypeId()):
			if 'тамп' in doc.GetElement(e.GetTypeId()).get_Parameter(BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM).AsString():
				i[5] = '-' + doc.GetElement(e.GetTypeId()).get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()

string = ' ----------- OK -----------\n'
for i in lst:
	for j in i:
		string += '{}'.format(j if type(j) == str else j.Name) + ", "
	string += '\n'

t = Transaction(doc, "Нумератор листов")
err = ''
t.Start()
for index, i in enumerate(lst):
	i[0].LookupParameter('Номер листа').Set('w' + i[1])
for i in lst:
	i[0].LookupParameter('Номер листа').Set(i[2] + i[4] + i[5])
	try: i[0].LookupParameter('ХТ Номер листа').Set(i[4])
	except: err = 'Параметр "ХТ Номер листа" не существует, значение не присвоено.\n'
t.Commit()

print(err + string)


