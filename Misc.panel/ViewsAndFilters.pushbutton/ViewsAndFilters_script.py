# -*- coding: utf-8 -*-
""""""
__title__ = 'Виды и\nфильтры'
__author__ = 'SG'

import os
import sys
import re
import clr
clr.AddReference('System.Core')
from System.Collections.Generic import *
from Autodesk.Revit.DB import ElementId, FilteredElementCollector, BuiltInCategory, Transaction, BuiltInParameter, ParameterFilterElement, ElementParameterFilter, ViewDuplicateOption
from Autodesk.Revit.DB import Color, LinePatternElement, FillPatternElement, ParameterFilterRuleFactory, ParameterElement, InternalDefinition, LabelUtils, SharedParameterElement
from Autodesk.Revit.DB import LogicalOrFilter, LogicalAndFilter
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from pyrevit import script
# from Autodesk.Revit.ApplicationServices.Application import Create
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
k = 304.8


def natural_sorted(list, key=lambda s: s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        convert = lambda text: int(text) if text.isdigit() else text  # noqa
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    return sorted(list, key=sort_key)


cats = {}
for cat in doc.Settings.Categories:
    # print('{} {}'.format(cat.Id.IntegerValue, cat.Name))
    cats[cat.Id.IntegerValue] = (cat, cat.Name)
    if cat.SubCategories:
        for subcat in cat.SubCategories:
            # print('{} {}'.format(subcat.Id.IntegerValue, subcat.Name))
            cats[subcat.Id.IntegerValue] = (subcat, subcat.Name)

cat_names = [cats[i][1] for i in cats]
twins = []
for name in cat_names:
    if cat_names.count(name) > 1:
        twins.append(name)

cats_by_name = {}
for key in cats:  # Name individualizing
    cat = cats[key][0]
    name = cats[key][1]
    new_name = name
    if name in twins:
        new_name = name + ' [' + str(key) + ']'
        cats[key] = (cat, new_name)
        # print(new_name)
    cats_by_name[new_name] = cat

builtin_params = {}
for i in dir(BuiltInParameter):
    try:
        bip = getattr(BuiltInParameter, i)
        name = LabelUtils.GetLabelFor(bip)
        builtin_params[ElementId(bip).IntegerValue] = (bip, name)
    except:
        pass

builtin_param_names = [builtin_params[i][1] for i in builtin_params]
twins = []
for name in builtin_param_names:
    if builtin_param_names.count(name) > 1:
        twins.append(name)

builtin_params_by_name = {}
for key in builtin_params:  # Name individualizing
    bip = builtin_params[key][0]
    name = builtin_params[key][1]
    new_name = name
    if name in twins:
        new_name = name + ' [' + str(key) + ']'
        builtin_params[key] = (bip, new_name)
    builtin_params_by_name[new_name] = bip

project_params = {}
iterator = doc.ParameterBindings.ForwardIterator()
iterator.Reset()
while(iterator.MoveNext()):
    param = iterator.Key
    project_params[param.Id.IntegerValue] = (param, param.Name)

project_param_names = [project_params[i][1] for i in project_params]

twins = []
for name in project_param_names:
    if project_param_names.count(name) > 1:
        twins.append(name)

project_params_by_name = {}
for key in project_params:  # Name individualizing
    param = project_params[key][0]
    name = project_params[key][1]
    new_name = name
    if name in twins:
        new_name = name + ' [' + str(key) + ']'
        project_params[key] = (param, new_name)
    project_params_by_name[new_name] = param


def get_param_name(param_id):
    # print(param_id)
    if param_id.IntegerValue < 0:
        param_name = builtin_params[param_id.IntegerValue][1]
    else:
        param_name = project_params[param_id.IntegerValue][1]
        # param_name = doc.GetElement(param_id).Name
    return param_name


evaluator_signs = {'FilterNumericEquals'         : 'n=',   # равно            (число)   # noqa
                   'FilterNumericEquals-'        : 'n!=',  # не равно         (число)   # noqa
                   'FilterNumericGreater'        : 'n>',   # больше           (число)   # noqa
                   'FilterNumericGreaterOrEqual' : 'n>=',  # больше или равно (число)   # noqa
                   'FilterNumericLess'           : 'n<',   # меньше           (число)   # noqa
                   'FilterNumericLessOrEqual'    : 'n<=',  # меньше или равно (число)   # noqa
                   'FilterStringEquals'          : '=',   # равно                      # noqa
                   'FilterStringEquals-'         : '!=',  # не равно                   # noqa
                   'FilterStringGreater'         : '>',   # больше                     # noqa
                   'FilterStringGreaterOrEqual'  : '>=',  # больше или равно           # noqa
                   'FilterStringLess'            : '<',   # меньше                     # noqa
                   'FilterStringLessOrEqual'     : '<=',  # меньше или равно           # noqa
                   'FilterStringContains'        : '^',   # содержит                   # noqa
                   'FilterStringContains-'       : '!^',  # не содержит                # noqa
                   'FilterStringBeginsWith'      : '<<',  # начинается с               # noqa
                   'FilterStringBeginsWith-'     : '!<',  # не начинается с            # noqa
                   'FilterStringEndsWith'        : '>>',  # заканчивается на           # noqa
                   'FilterStringEndsWith-'       : '!>',  # не заканчивается на        # noqa
                  }

pfrf = ParameterFilterRuleFactory
evaluator_methods = {'n=' : pfrf.CreateEqualsRule          ,# равно                      # noqa
                     'n!=': pfrf.CreateNotEqualsRule       ,# не равно                   # noqa
                     'n>' : pfrf.CreateGreaterRule         ,# больше                     # noqa
                     'n>=': pfrf.CreateGreaterOrEqualRule  ,# больше или равно           # noqa
                     'n<' : pfrf.CreateLessRule            ,# меньше                     # noqa
                     'n<=': pfrf.CreateLessOrEqualRule     ,# меньше или равно           # noqa
                     '=' : pfrf.CreateEqualsRule          ,# равно                      # noqa
                     '!=': pfrf.CreateNotEqualsRule       ,# не равно                   # noqa
                     '>' : pfrf.CreateGreaterRule         ,# больше                     # noqa
                     '>=': pfrf.CreateGreaterOrEqualRule  ,# больше или равно           # noqa
                     '<' : pfrf.CreateLessRule            ,# меньше                     # noqa
                     '<=': pfrf.CreateLessOrEqualRule     ,# меньше или равно           # noqa
                     '^' : pfrf.CreateContainsRule        ,# содержит                   # noqa
                     '!^': pfrf.CreateNotContainsRule     ,# не содержит                # noqa
                     '<<': pfrf.CreateBeginsWithRule      ,# начинается с               # noqa
                     '!<': pfrf.CreateNotBeginsWithRule   ,# не начинается с            # noqa
                     '>>': pfrf.CreateEndsWithRule        ,# заканчивается на           # noqa
                     '!>': pfrf.CreateNotEndsWithRule     ,# не заканчивается на        # noqa
                     }

# sys.exit()

all_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()
all_filters = natural_sorted(all_filters, key=lambda x: x.Name)
data = []
for filt in all_filters:
    d = []
    d.append(str(filt.Id))
    d.append(str(filt.Name))
    arrr = [cats[elid.IntegerValue][1] for elid in filt.GetCategories()]
    d.append(str('; '.join(sorted(arrr))))
    # print('{} {}'.format('filt ' + filt.Name, filt.))
    # for i in dir(filt):
    #     print(i)
    # sys.exit()
    logical_filter = filt.GetElementFilter()
    # d.append(str(logical_filter))
    if logical_filter:
        i = 1
        dd = []
        dd.append(logical_filter.__class__.__name__)
        for epfilter in logical_filter.GetFilters():
            for rule in epfilter.GetRules():
                rulename = rule.__class__.__name__
                invert = ''
                if rulename == 'FilterInverseRule':
                    rule = rule.GetInnerRule()
                    # rulename = rule.__class__.__name__ + ' I'
                    invert = '-'
                param_id = rule.GetRuleParameter()
                param_name = get_param_name(param_id)
                evaluator = evaluator_signs.get(str(rule.GetEvaluator().__class__.__name__) + invert, 'Error')
                try:
                    value = '{:.5f}'.format(rule.RuleValue)
                except AttributeError:
                    value = str(rule.RuleString)
                except ValueError:
                    value = str(rule.RuleValue)
                    if type(rule.RuleValue) == ElementId:
                        value = '[id' + str(rule.RuleValue) + ']'
                string = '{}: "{}" {} "{}"'.format(i, param_name, evaluator, value)
                i += 1
                dd.append(string)
        d.append(str('; '.join(dd)))
    # else:
    #     d.append('-')
    data.append(d)

columns = ['Id фильтра',
           'Имя фильтра',
           'Категории',
           'Правила']

output = script.get_output()
output.print_table(table_data=data, columns=columns)

# sys.exit()

views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
views = [i for i in views if i.Origin]
views = natural_sorted(views, key=lambda x: x.Name)
views = sorted(views, key=lambda x: x.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM).AsValueString())
data = []
for view in views:
    view_filters = [doc.GetElement(i) for i in view.GetFilters()]
    for view_filter in view_filters:
        d = []
        d.append(str(view.Id))
        d.append(view.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM).AsValueString())
        d.append(view.Name)
        d.append(str(view_filter.Id))
        d.append(str(view_filter.Name))
        d.append(str(1 if view.GetFilterVisibility(view_filter.Id) else 0))
        cfg = view.GetFilterOverrides(view_filter.Id)
        d.append(str(cfg.ProjectionLineWeight))
        d.append(str('{} {} {}'.format(cfg.ProjectionLineColor.Red, cfg.ProjectionLineColor.Green, cfg.ProjectionLineColor.Blue) if cfg.ProjectionLineColor.IsValid else '-1'))
        d.append(str(doc.GetElement(cfg.ProjectionLinePatternId).Name if cfg.ProjectionLinePatternId.IntegerValue > 0 else '-1'))
        d.append(str(1 if cfg.IsProjectionFillPatternVisible else 0))
        d.append(str(doc.GetElement(cfg.ProjectionFillPatternId).Name if cfg.ProjectionFillPatternId.IntegerValue > 0 else '-1'))
        d.append(str('{} {} {}'.format(cfg.ProjectionFillColor.Red, cfg.ProjectionFillColor.Green, cfg.ProjectionFillColor.Blue) if cfg.ProjectionFillColor.IsValid else '-1'))
        d.append(str(cfg.Transparency))
        d.append(str(cfg.CutLineWeight))
        d.append(str('{} {} {}'.format(cfg.CutLineColor.Red, cfg.CutLineColor.Green, cfg.CutLineColor.Blue) if cfg.CutLineColor.IsValid else '-1'))
        d.append(str(doc.GetElement(cfg.CutLinePatternId).Name if cfg.CutLinePatternId.IntegerValue > 0 else '-1'))
        d.append(str(1 if cfg.IsCutFillPatternVisible else 0))
        d.append(str(doc.GetElement(cfg.CutFillPatternId).Name if cfg.CutFillPatternId.IntegerValue > 0 else '-1'))
        d.append(str('{} {} {}'.format(cfg.CutFillColor.Red, cfg.CutFillColor.Green, cfg.CutFillColor.Blue) if cfg.CutFillColor.IsValid else '-1'))
        d.append(str(1 if cfg.Halftone else 0))
        data.append(d)

columns = ['Id вида',
           'Тип вида',
           'Имя вида',
           'Id фильтра',
           'Имя фильтра',
           'Видимость',
           'Проекция. Линии. Вес',
           'Проекция. Линии. Цвет',
           'Проекция. Линии. Образец',
           'Проекция. Штриховки. Видимость',
           'Проекция. Штриховки. Образец',
           'Проекция. Штриховки. Цвет',
           'Проекция. Прозрачность',
           'Разрез. Линии. Вес',
           'Разрез. Линии. Цвет',
           'Разрез. Линии. Образец',
           'Разрез. Штриховки. Видимость',
           'Разрез. Штриховки. Образец',
           'Разрез. Штриховки. Цвет',
           'Полутона']

if not data:
    data = [columns]
output.print_table(table_data=data, columns=columns)

path = os.path.join(os.path.dirname(doc.PathName), 'ViewsAndFilters.txt')
try:
    src = open(path, 'r').read().decode("utf-8")
    if src:
        src = src[:-1] if src[-1] == '\n' else src
    if not src or src[0] == '\n':
        raise IOError
except IOError:
    info = '\n' + path + '\nЭтот файл должен содержать таблицу (разделители - табуляция).\nПервая строка должна содержать заголовки. Последняя строка может быть пустой.\n'
    with open(path, 'w') as file:
        file.write(info.encode("utf-8"))
    os.startfile(path)
    sys.exit()

if __shiftclick__:
        os.startfile(path)
        sys.exit()

src_filters, src_views = src.split('\n\n')


def get_cats(s):
    return [cats_by_name[name].Id for name in s.split('; ')]


def get_param(name):
    return project_params_by_name.get(name, None) or builtin_params_by_name.get(name, None)


# for i in project_params:
# print(project_params)
# print('; '.join([i for i in project_params]))

def create_rule(param, evaluator, value):
    # print(param)
    # print(evaluator)
    # print(value)
    # print(45555555555555555555555555555)
    # print(param.Name) if not isinstance(param, BuiltInParameter) else 11
    # print(isinstance(param, BuiltInParameter))
    param_id = ElementId(param) if isinstance(param, BuiltInParameter) else param.Id
    args = [param_id, value]
    if 'n' in evaluator:
        if '[id' in value:
            value = int(value.replace('[id', '').replace(']', ''))
            args[1] = ElementId(value)
        elif value.isdigit():
            args[1] = int(value)
        else:
            args[1] = float(value)
            args.append(0.00001)
    else:
        args.append(True)
    # print('{} {}'.format(evaluator_methods[evaluator], ' / / '.join(['{}({})'.format(str(i), type(i)) for i in args])))
    rule = evaluator_methods[evaluator](*args)
    return rule


def get_rules(s):
    result = []
    for part in s.split('; ')[1:]:
        # print(s)
        # print(part)
        param_name = part.split('"')[1]
        value = part.split('"')[3]
        evaluator = part.replace(' "' + param_name + '"', '').replace(' "' + value + '"', '').split()[1]
        param = get_param(param_name)
        # print(param)
        # print(param_name)
        rule = create_rule(param, evaluator, value)
        result.append(rule)
    return result

    # pfilter = parameterFilterElement = ParameterFilterElement.Create(
    #     doc,
    #     name + ' не',
    #     cats,
    #     ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(BuiltInParameter.RBS_SYSTEM_NAME_PARAM), name, True))
    # )

t = Transaction(doc, 'Виды и фильтры')
t.Start()

for string in src_filters.split('\n')[1:]:
    string = string.split('\t')
    filter_id =   ElementId(int(string[0]))
    filter_name =               string[1]
    cat_ids =          get_cats(string[2])
    and_logic =                 string[3].split('; ')[0] == 'LogicalAndFilter'
    rules =           get_rules(string[3])

    # cat_ids = [i.Id for i in cats]

    filt = [i for i in all_filters if i.Id == filter_id][0]
    filt.SetCategories(List[ElementId](cat_ids))
    # print(filter_name)

    epfilters = []
    for rule in rules:
        epfilters.append(ElementParameterFilter(rule))

    # i = 1
    # curr_cats = '; '.join(sorted([cats[elid.IntegerValue][1] for elid in filt.GetCategories()]))
    # for epfilter in filt.GetElementFilter().GetFilters():
    #     for rule in epfilter.GetRules():
    #         rulename = rule.__class__.__name__
    #         invert = ''
    #         if rulename == 'FilterInverseRule':
    #             rule = rule.GetInnerRule()
    #             # rulename = rule.__class__.__name__ + ' I'
    #             invert = '-'
    #         param_id = rule.GetRuleParameter()
    #         param_name = get_param_name(param_id)
    #         evaluator = evaluator_signs.get(str(rule.GetEvaluator().__class__.__name__) + invert, 'Error')
    #         try:
    #             value = '{:.5f}'.format(rule.RuleValue)
    #         except AttributeError:
    #             value = str(rule.RuleString)
    #         except ValueError:
    #             value = str(rule.RuleValue)
    #             if type(rule.RuleValue) == ElementId:
    #                 value = '[id' + str(rule.RuleValue) + ']'
    #         string = '{}: {}: "{}" {} "{}"'.format(i, curr_cats, param_name, evaluator, value)
    #         i += 1
    #         print(string)

    # i = 1
    # new_cats = '; '.join(sorted([cats[elid.IntegerValue][1] for elid in cat_ids]))
    # epfilter = ElementParameterFilter(rules)  #################################################################### не комментировать! уже можно?
    # print(epfilter)
    # # for epfilter in filt.GetElementFilter().GetFilters():
    # for rule in epfilter.GetRules():
    #     rulename = rule.__class__.__name__
    #     invert = ''
    #     if rulename == 'FilterInverseRule':
    #         rule = rule.GetInnerRule()
    #         # rulename = rule.__class__.__name__ + ' I'
    #         invert = '-'
    #     param_id = rule.GetRuleParameter()
    #     param_name = get_param_name(param_id)
    #     evaluator = evaluator_signs.get(str(rule.GetEvaluator().__class__.__name__) + invert, 'Error')
    #     try:
    #         value = '{:.5f}'.format(rule.RuleValue)
    #     except AttributeError:
    #         value = str(rule.RuleString)
    #     except ValueError:
    #         value = str(rule.RuleValue)
    #         if type(rule.RuleValue) == ElementId:
    #             value = '[id' + str(rule.RuleValue) + ']'
    #     string = '{}: {}: "{}" {} "{}"'.format(i, new_cats, param_name, evaluator, value)
    #     i += 1
    #     print(string)
    lfilter = LogicalAndFilter(epfilters) if and_logic else LogicalOrFilter(epfilters)
    filt.SetElementFilter(lfilter)

#     pfilter = parameterFilterElement = ParameterFilterElement.Create(
#         doc,
#         name + ' не',
#         cats,
#         ElementParameterFilter(ParameterFilterRuleFactory.CreateNotEqualsRule(ElementId(BuiltInParameter.RBS_SYSTEM_NAME_PARAM), name, True))
#     )


def col(s):
    arr = [int(i) for i in s.split()]
    return Color(*arr) if len(arr) == 3 else None


def line(s):
    if s == '-1':
        return None
    all_patterns = FilteredElementCollector(doc).OfClass(LinePatternElement).ToElements()
    # print(s)
    return [i for i in all_patterns if i.Name == s][0].Id


def fill(s):
    if s == '-1':
        return None
    all_patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    return [i for i in all_patterns if i.Name == s][0].Id


for string in src_views.split('\n')[1:]:
    string = string.split('\t')
    view_id =                                  ElementId(int(string[0]))
    view_symbol =                                            string[1]
    view_name =                                              string[2]
    view_filter_id =                           ElementId(int(string[3]))
    view_filter_name =                                       string[4]
    filter_visibility =                             bool(int(string[5]))
    projectionLineWeight =                               int(string[6])
    projectionLineColor =                                col(string[7])
    projectionLinePatternId =                           line(string[8])
    isProjectionFillPatternVisible =                bool(int(string[9]))
    projectionFillPatternId =                           fill(string[10])
    projectionFillColor =                                col(string[11])
    transparency =                                       int(string[12])
    cutLineWeight =                                      int(string[13])
    cutLineColor =                                       col(string[14])
    cutLinePatternId =                                  line(string[15])
    isCutFillPatternVisible =                       bool(int(string[16]))
    cutFillPatternId =                                  fill(string[17])
    cutFillColor =                                       col(string[18])
    halftone =                                      bool(int(string[19]))


    view = doc.GetElement(view_id)
    view_filter = doc.GetElement(view_filter_id)
    cfg = view.GetFilterOverrides(view_filter.Id)
    # cfg = OverrideGraphicSettings()
    view.SetFilterVisibility(view_filter_id, filter_visibility)
    cfg.SetProjectionLineWeight(projectionLineWeight) if projectionLineWeight > 0 else None
    cfg.SetProjectionLineColor(projectionLineColor) if projectionLineColor else None
    cfg.SetProjectionLinePatternId(projectionLinePatternId) if projectionLinePatternId else None
    cfg.SetProjectionFillPatternVisible(isProjectionFillPatternVisible)
    cfg.SetProjectionFillPatternId(projectionFillPatternId) if projectionFillPatternId else None
    cfg.SetProjectionFillColor(projectionFillColor) if projectionFillColor else None
    cfg.SetSurfaceTransparency(transparency)
    cfg.SetCutLineWeight(cutLineWeight) if cutLineWeight > 0 else None
    cfg.SetCutLineColor(cutLineColor) if cutLineColor else None
    cfg.SetCutLinePatternId(cutLinePatternId) if cutLinePatternId else None
    cfg.SetCutFillPatternVisible(isCutFillPatternVisible)
    cfg.SetCutFillPatternId(cutFillPatternId) if cutFillPatternId else None
    cfg.SetCutFillColor(cutFillColor) if cutFillColor else None
    cfg.SetHalftone(halftone)
    view.SetFilterOverrides(view_filter_id, cfg)

t.Commit()