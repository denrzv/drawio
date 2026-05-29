# drawio decoder
import xml.etree.ElementTree as ET
import re
import base64
import zlib
from urllib.parse import quote, unquote

# args
import sys, getopt
from pathlib import Path

def js_encode_uri_component(data):
    return quote(data, safe='~()*!.\'')


def js_decode_uri_component(data):
    return unquote(data)


def js_string_to_byte(data):
    return bytes(data, 'iso-8859-1')


def js_bytes_to_string(data):
    return data.decode('iso-8859-1')


def js_btoa(data):
    return base64.b64encode(data)


def js_atob(data):
    return base64.b64decode(data)

def pako_inflate_raw(data):
    decompress = zlib.decompressobj(-15)
    decompressed_data = decompress.decompress(data)
    decompressed_data += decompress.flush()
    return decompressed_data

# diagram elements
class Object:
    def __init__(self,attributes):
        self.id = None
        setattr(self, 'c4Name', '')
        for key in attributes.keys():
            if key == 'id':
                self.id = attributes[key]
            if key.startswith('c4'):
                setattr(self, key, attributes[key])
            if key.lower()=='cmdb':
                setattr(self, 'cmdb', attributes[key])

    def print(self):
        for key in self.__dict__.keys():
            print(key, ':', getattr(self, key))

class Relation (Object):
    def __init__(self,source,target, attributes):
        super().__init__(attributes)
        self.source = source
        self.target = target


    def print(self):
        return super().print()

class BrokenRelation (Object):
    def __init__(self, attributes):
        self.source = None
        self.target = None
        self.source_point = None
        self.target_point = None
        super().__init__(attributes)

    def print(self):
        if self.source_point is not None:
            print(f'source point: {self.source_point[0]}, {self.source_point[1]}')
        if self.target_point is not None:
            print(f'target point: {self.target_point[0]}, {self.target_point[1]}')
        return super().print()

class Element (Object):
    def __init__(self,attributes):
        self.left_top = None
        self.right_bottom = None
        self.parent_id = None
        super().__init__(attributes)

    def is_element_inside(self,parent_element):
        if parent_element.left_top is None or parent_element.right_bottom is None:
            return False
        if self.left_top is None or self.right_bottom is None:
            return False
        if self.left_top[0] >= parent_element.left_top[0] and self.left_top[1] >= parent_element.left_top[1] and self.right_bottom[0] <= parent_element.right_bottom[0] and self.right_bottom[1] <= parent_element.right_bottom[1]:
            return True
        return False

# function that export to Structurizr DSL

_SYMBOLS_FROM = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA_"
_SYMBOLS_TO   = u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA_abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA_"
_TRANS_MAP = {_SYMBOLS_FROM[i]: _SYMBOLS_TO[i] for i in range(len(_SYMBOLS_FROM))}

def create_var_name(name, dubles, deep):
    src = name.lower()
    parts = []
    for c in src:
        if c in _TRANS_MAP:
            parts.append(_TRANS_MAP[c])
        elif c.isalnum():
            parts.append(c)
        else:
            parts.append('_')
    res = re.sub(r'_+', '_', ''.join(parts)).strip('_')
    if not res:
        res = 'var'

    if res in dubles:
        new_res = res + str(len(dubles[res]))
        dubles[res].append(new_res)
        res = new_res
    else:
        dubles[res] = [res]

    return res

def recurse_walk(components, children_map, relations, file, component, deep, names, visible_names, dubles, visited):
    if component.id in visited:
        return
    visited.add(component.id)
    child_count = 0

    id   = component.id
    name = component.c4Name.replace("\n"," ")
    if len(name)==0:
        name = component.c4Type.replace("\n"," ")

    if name in visible_names:
        new_name = name + '_'+str(len(visible_names[name]))
        visible_names[name].append(new_name)
        name = new_name
    else:
        visible_names[name] = list()

    var_name = create_var_name(name, dubles, deep)
    var_type = 'system'

    if 'c4Type' in component.__dict__:
        if component.c4Type != None:
            var_type = component.c4Type

    indent = '    ' * deep
    if deep == 1:
        if var_type == 'Person':
            file.write(indent + var_name + ' = Person "' + name + '" {\n')
        else:
            file.write(indent + var_name + ' = softwareSystem "' + name + '" {\n')
            if hasattr(component, 'cmdb'):
                file.write(indent + '    properties {\n')
                file.write(indent + '        cmdb ' + component.cmdb + '\n')
                file.write(indent + '    }\n')
    elif deep == 2:
        file.write(indent + var_name + ' = container "' + name + '" {\n')
    elif deep == 3:
        file.write(indent + var_name + ' = component "' + name + '" {\n')

    if 'c4Description' in component.__dict__ and component.c4Description is not None:
        file.write(indent + '    description "' + component.c4Description.replace("\n", " ") + '"\n')

    if 'c4Technology' in component.__dict__ and component.c4Technology is not None:
        file.write(indent + '    technology "' + component.c4Technology.replace("\n", " ") + '"\n')

    for comp in children_map.get(id, []):
        recurse_walk(components, children_map, relations, file, comp, deep + 1, names, visible_names, dubles, visited)
        child_count += 1

    names.append([var_name, deep, child_count, id])

    file.write(indent + '}\n')



def export_to_dsl(components, relations):

    with open("workspace.dsl", "w") as file:
        file.write("workspace {\n")
        file.write("model {\n")
        names = list()
        visible_names = dict()
        dubles = dict()

        children_map = {}
        for comp in components.values():
            pid = comp.parent_id
            children_map.setdefault(pid, []).append(comp)

        visited = set()
        for comp in components.values():
            if comp.parent_id is None:
                recurse_walk(components, children_map, relations, file, comp, 1,
                             names, visible_names, dubles, visited)

        elements = {n[3]: n for n in names}

        for rel in relations:
            if rel.source not in elements or rel.target not in elements:
                rel_name = getattr(rel, 'c4Description', '').replace("\n", " ") or rel.id
                print(f'Предупреждение: пропуск связи "{rel_name}" — компонент не найден в модели')
                continue
            rel_name = getattr(rel, 'c4Description', '').replace("\n", " ")
            if not rel_name:
                rel_name = 'Вызов'
            rel_technology = getattr(rel, 'c4Technology', '').replace("\n", " ")
            if not rel_technology:
                rel_technology = 'unknown'
            file.write("    " + elements[rel.source][0] + " -> " +
                        elements[rel.target][0] + ' "' + rel_name + '" "' + rel_technology + '"\n')

        file.write("}\n")
        file.write("views {\n")

        file.write("    systemLandscape {\n")
        file.write("        include *\n")
        file.write("        autoLayout\n")
        file.write("    }\n")

        for n in names:
            if n[2]>0 : # have childs
                if n[1] == 1:
                    file.write("    container "+n[0]+" {\n")
                    file.write("        include *\n")
                    file.write("        autoLayout\n")
                    file.write("    }\n")
                elif n[1] == 2:
                    file.write("    component "+n[0]+" {\n")
                    file.write("        include *\n")
                    file.write("        autoLayout\n")
                    file.write("    }\n")


        file.write("    themes default\n")
        file.write("    }\n")
        file.write("}\n")

# helper function to get coordinates
def get_coordinates(collection):
    coordinates = []
    coordinates.append(float(0))
    coordinates.append(float(0))
    if 'x' in collection.keys():
        coordinates[0] = float(collection['x'])
    if 'y' in collection.keys():
        coordinates[1] = float(collection['y'])
    return coordinates

# function that load from xml (.drawio)
def load_from_xml(filename,print_statistics):
    xml = open(filename).read()
    components = {}
    relations = []
    broken_relations = []

    xml_document = ET.ElementTree(ET.fromstring(xml))
    diagram_element = xml_document.find("diagram")

    if not diagram_element is None:
        if list(diagram_element): # unencoded
            root_node =list(diagram_element)[0]
            #print(ET.tostring(root_node))
        else: # encoded
            b64 = diagram_element.text
            a = base64.b64decode(b64)
            b = pako_inflate_raw(a)
            c = js_decode_uri_component(b.decode())
            #print(c)
            root_node = ET.ElementTree(ET.fromstring(c))

        for d in root_node.findall('root/object'):
            if 'c4Type' in d.attrib:
                # parse c4 relations
                if d.attrib['c4Type'] == 'Relationship':
                    mx_cell = d.find('mxCell')
                    if(mx_cell is not None):
                        have_source = False
                        have_target = False
                        source = None
                        target = None
                        if 'source' in mx_cell.attrib:
                            source = mx_cell.attrib['source']
                            have_source = True
                        if 'target' in mx_cell.attrib:
                            target = mx_cell.attrib['target']
                            have_target = True

                        if have_source and have_target: 
                            rel = Relation(source, target,d.attrib)
                            if not 'c4Description' in d.attrib:
                                rel.__setattr__('c4Description','')
                            if not 'c4Name' in d.attrib:
                                rel.__setattr__('c4Name','')
                            if not 'c4Technology' in d.attrib:
                                rel.__setattr__('c4Technology','')       
                            relations.append(rel)
                        else:
                            # case then component have no source or target
                            broken_relation = BrokenRelation(d.attrib)
                            if have_source:
                                broken_relation.source = source
                            if have_target:
                                broken_relation.target = target

                            # try to get infoermation of source and target point from relations
                            geom = mx_cell.find('mxGeometry')
                            if geom is not None:
                                points = geom.findall('mxPoint')
                                for p in points:
                                    if 'as' in p.attrib:
                                        if p.attrib['as'] == 'source' or p.attrib['as'] == 'sourcePoint':
                                            broken_relation.source_point = get_coordinates(geom.attrib)
                                        if p.attrib['as'] == 'target' or p.attrib['as'] == 'targetPoint':
                                            broken_relation.target_point = get_coordinates(geom.attrib)
                            if(not 'c4Description' in d.attrib):
                                broken_relation.__setattr__('c4Description','')
                            if(not 'c4Name' in d.attrib):
                                broken_relation.__setattr__('c4Name','')
                            if(not 'c4Technology' in d.attrib):
                                broken_relation.__setattr__('c4Technology','')
                            broken_relations.append(broken_relation)
                else:
                    # parse c4 components
                    comp = Element(d.attrib)

                    mx_cell = d.find('mxCell')
                    if(mx_cell is not None):
                        geom = mx_cell.find('mxGeometry')
                        if geom is not None:
                            comp.left_top = get_coordinates(geom.attrib)
                            comp.right_bottom = [comp.left_top[0] + float(geom.attrib['width']),comp.left_top[1] + float(geom.attrib['height'])]
                    components[comp.id] = comp

        # parse labels and edges for non-c4 relations            
        labels = {}
        for d in root_node.findall('root/mxCell'):   
            if 'style' in d.attrib:
                # parse edge
                if d.attrib['style'].find('edgeStyle=') != -1:
                    broken_relation = BrokenRelation({})
                    broken_relation.id = d.attrib['id']
                    if 'source' in d.attrib:
                        broken_relation.source = d.attrib['source']
                    if 'target' in d.attrib:
                        broken_relation.target = d.attrib['target']
                    broken_relation.__setattr__('c4Name','')
                    broken_relation.__setattr__('c4Type','Relationship')
                    broken_relation.__setattr__('c4Technology','')
                    broken_relation.__setattr__('c4Description','')
                    broken_relations.append(broken_relation)
            
            # parse label
            if 'style' in d.attrib:
                if d.attrib['style'].find('edgeLabel') != -1:
                    if( 'parent' in d.attrib) and ('value' in d.attrib):
                            labels[d.attrib['parent']] = d.attrib['value']

        # parse technology from non c4-relations labels
        broken_relations_by_id = {br.id: br for br in broken_relations}
        for label_id, label_value in labels.items():
            br = broken_relations_by_id.get(label_id)
            if br is not None:
                br.c4Description = label_value
                m = re.search(r'\[(.*)\]', label_value)
                if m:
                    br.c4Technology = m.group(1)

    if print_statistics==True:
        print('Number of components: ' + str(len(components)))
        print('Number of relations: ' + str(len(relations)))
        print('Number of broken relations: ' + str(len(broken_relations)))


    return components, relations ,broken_relations

# remove relationship that links to component that not in component list
def fix_missing_relations(components,relations):
    result_relations = []
    for rel in relations:
        if rel.source not in components.keys():
            rel.source = None
        if rel.target not in components.keys():
            rel.target = None

        if rel.source is not None and rel.target is not None:
            result_relations.append(rel)
    return result_relations

# fix broken relations
def fix_broken_relations(components,relations,broken_relations):
    i = 0
    for broken_relation in broken_relations:
        if broken_relation.source is None and broken_relation.source_point is not None:
            candidats = {}
            for comp in components.values():
                if comp.left_top[0] <= broken_relation.source_point[0] <= comp.right_bottom[0] and comp.left_top[1] <= broken_relation.source_point[1] <= comp.right_bottom[1]:                                       
                    candidats[(comp.right_bottom[0]-comp.left_top[0])*(comp.right_bottom[1]-comp.left_top[1])] = comp.id;                  
                    
            if len(candidats) > 0:
                broken_relation.source = candidats[min(candidats.keys())]

        if broken_relation.target is None and broken_relation.target_point is not None:
            candidats = {}
            for comp in components.values():
                if comp.left_top[0] <= broken_relation.target_point[0] <= comp.right_bottom[0] and comp.left_top[1] <= broken_relation.target_point[1] <= comp.right_bottom[1]:
                    candidats[(comp.right_bottom[0]-comp.left_top[0])*(comp.right_bottom[1]-comp.left_top[1])] = comp.id;  
                    
            if len(candidats) > 0:
                broken_relation.target = candidats[min(candidats.keys())]

        if broken_relation.source is not None and broken_relation.target is not None:
            i = i + 1
            #print(broken_relation.__dict__)
            relations.append(Relation(broken_relation.source,broken_relation.target,broken_relation.__dict__))
            
    return relations

# function that print broken relations
def print_broken_relations(broken_relations,i):
    for br in broken_relations:
        print(f'{i}. Связь {br.id} "{br.c4Name}" не имеет начала или конца "{br.c4Description}"')
        if br.source is not None:
            print(f'Начало: {br.source}')
        if br.target is not None:
            print(f'Конец: {br.target}')
        
        if br.source_point is not None:
            print(f'Начало: {br.source_point}')
        if br.target_point is not None:
            print(f'Конец: {br.target_point}')
        i = i+1
    return i

# function that check relations
def check_relations(components, relations,i,check_data):
    def component_name(component):
        if len(component.c4Name)!=0:
            return component.c4Name.replace('\n',' ')
        else:
            return component.c4Type+":"+component.c4Description.replace('\n',' ')

    def relation_name(relation):
        if(len(relation.c4Description.rstrip())>0):
            # return relation.c4Description with replaced newlines
            return relation.c4Description.replace('\n',' ')
        else:
            return ''

    for rel in relations:
        if rel.source not in components:
            print(f'Для связи "{relation_name(rel)}" отсутствует стартовый компонент')
        if rel.target not in components:
            print(f'Для связи "{relation_name(rel)}" отсутствует конечный компонент')
        if 'c4Technology' in rel.__dict__:
            if rel.c4Technology=='' and components[rel.source].c4Type != 'Person' and components[rel.target].c4Type != 'Person':
                print(f'{i}. Для связи "{relation_name(rel)}" между "{component_name(components[rel.source])}" и "{component_name(components[rel.target])}" не указана технология')
                i = i + 1
        if 'c4Description' in rel.__dict__ and check_data:
            m = re.search(r'\((.*)\)', rel.c4Description)
            if m is None:
                if components[rel.source].c4Type != 'Person' and components[rel.target].c4Type != 'Person':
                    print(f'{i}. Для связи "{relation_name(rel)}" между "{component_name(components[rel.source])}" и "{component_name(components[rel.target])}" не указаны входные данные')
                    i = i + 1
            m = re.search(r'\):(.*)', rel.c4Description)
            if m is None:
                if components[rel.source].c4Type != 'Person' and components[rel.target].c4Type != 'Person':
                    print(f'{i}. Для связи "{relation_name(rel)}" между "{component_name(components[rel.source])}" и "{component_name(components[rel.target])}" не указаны возвращаемые данные')
                    i = i + 1
    return i

# function that fills parent id
def fill_parent_id(components):
    result = {}
    for comp in components.values():
        best_parent_id = None
        best_area = float('inf')
        for parent in components.values():
            if comp is parent:
                continue
            if comp.is_element_inside(parent):
                w = parent.right_bottom[0] - parent.left_top[0]
                h = parent.right_bottom[1] - parent.left_top[1]
                area = w * h
                if area < best_area:
                    best_area = area
                    best_parent_id = parent.id
        comp.parent_id = best_parent_id
        result[comp.id] = comp
    return result

# function that checks inpound and outbound relations
# if component has a parent, the parent must have inbound or outbound relation
def check_inbound_outbound_relations(comp, components, connected_ids):
    if comp.id in connected_ids:
        return True
    if comp.parent_id is not None and comp.parent_id in components:
        return check_inbound_outbound_relations(components[comp.parent_id], components, connected_ids)
    return False


# function that checks components
def check_components(components, relations, i):
    connected_ids = set()
    for rel in relations:
        connected_ids.add(rel.source)
        connected_ids.add(rel.target)

    for comp in components.values():
        if 'c4Description' not in comp.__dict__:
            if comp.c4Type != 'SystemScopeBoundary' and comp.c4Type != 'ContainerScopeBoundary' and comp.c4Type != 'Person':
                print(f'{i}. {comp.c4Type} "{comp.c4Name}" не указано описание')
                i = i + 1
        if 'c4Technology' not in comp.__dict__:
            if(comp.c4Type != 'Software System') and (comp.c4Type != 'Person') and (comp.c4Type != 'SystemScopeBoundary') and (comp.c4Type != 'ContainerScopeBoundary'):
                print(f'{i}. {comp.c4Type} "{comp.c4Name}" не указана технология')
                i = i + 1

        if comp.c4Type != 'SystemScopeBoundary' and comp.c4Type != 'Person' and comp.c4Type != 'ContainerScopeBoundary':
            if check_inbound_outbound_relations(comp, components, connected_ids) is False:
                print(f'{i}. {comp.c4Type} "{comp.c4Name}" не имеет входящих и исходящих связей')
                i = i + 1
    return i


def process_drawio_file(inputfile, print_statistics):
    components, relations, broken_relations = load_from_xml(inputfile, print_statistics)
    components = fill_parent_id(components)
    relations = fix_broken_relations(components, relations, broken_relations)
    relations = fix_missing_relations(components, relations)
    return components, relations


def normalized_component_type(component):
    component_type = getattr(component, 'c4Type', '')
    if component_type == 'SystemScopeBoundary':
        return 'Software System'
    if component_type == 'ContainerScopeBoundary':
        return 'Container'
    return component_type


def component_merge_key(component):
    return (
        normalized_component_type(component),
        getattr(component, 'c4Name', ''),
    )


def merge_component_attributes(target, source):
    for key, value in source.__dict__.items():
        if key in ('id', 'parent_id', 'left_top', 'right_bottom'):
            continue
        if not hasattr(target, key) or getattr(target, key) in (None, ''):
            setattr(target, key, value)


def merge_models(model_parts):
    merged_components = {}
    component_ids_by_key = {}
    merged_relations = []
    relation_keys = set()

    for components, relations in model_parts:
        id_map = {}

        for component in components.values():
            key = component_merge_key(component)
            if key in component_ids_by_key:
                canonical_id = component_ids_by_key[key]
                merge_component_attributes(merged_components[canonical_id], component)
            else:
                canonical_id = component.id
                component_ids_by_key[key] = canonical_id
                merged_components[canonical_id] = component
            id_map[component.id] = canonical_id

        for component in components.values():
            canonical_component = merged_components[id_map[component.id]]
            if component.parent_id in id_map:
                canonical_component.parent_id = id_map[component.parent_id]

        for relation in relations:
            if relation.source not in id_map or relation.target not in id_map:
                continue
            source = id_map[relation.source]
            target = id_map[relation.target]
            relation_key = (
                source,
                target,
                getattr(relation, 'c4Description', ''),
                getattr(relation, 'c4Technology', ''),
            )
            if relation_key in relation_keys:
                continue
            relation.source = source
            relation.target = target
            relation_keys.add(relation_key)
            merged_relations.append(relation)

    return merged_components, merged_relations


def component_display_name(component):
    name = getattr(component, 'c4Name', '').replace("\n", " ").strip()
    if name:
        return name
    return getattr(component, 'c4Type', 'Unnamed element').replace("\n", " ").strip() or 'Unnamed element'


def exported_element_kind(component, depth):
    component_type = getattr(component, 'c4Type', '')
    if depth == 1:
        if component_type == 'Person':
            return 'Person'
        return 'Software System'
    if depth == 2:
        return 'Container'
    if depth == 3:
        return 'Component'
    return f'Nested Element (depth {depth})'


def build_children_map(components):
    children_map = {}
    for comp in components.values():
        children_map.setdefault(comp.parent_id, []).append(comp)
    return children_map


def print_export_summary(components, relations):
    children_map = build_children_map(components)
    visited = set()
    element_paths = {}

    print('Exported elements:')

    def walk(component, depth, path):
        if component.id in visited:
            return
        visited.add(component.id)
        kind = exported_element_kind(component, depth)
        name = component_display_name(component)
        element_paths[component.id] = ' / '.join(path + [name])
        indent = '  ' * depth
        print(f'{indent}- {kind}: {name}')
        for child in children_map.get(component.id, []):
            walk(child, depth + 1, path + [name])

    roots = children_map.get(None, [])
    if roots:
        for root in roots:
            walk(root, 1, [])
    else:
        print('  (none)')

    print('Exported relationships:')
    if not relations:
        print('  (none)')
        return

    for relation in relations:
        source = element_paths.get(relation.source)
        target = element_paths.get(relation.target)
        if source is None and relation.source in components:
            source = component_display_name(components[relation.source])
        if target is None and relation.target in components:
            target = component_display_name(components[relation.target])
        source = source or relation.source or 'unknown source'
        target = target or relation.target or 'unknown target'
        description = getattr(relation, 'c4Description', '').replace("\n", " ").strip() or 'Вызов'
        technology = getattr(relation, 'c4Technology', '').replace("\n", " ").strip()
        if technology:
            print(f'  - {source} -> {target}: {description} [{technology}]')
        else:
            print(f'  - {source} -> {target}: {description}')


def sanitize_file_name(name):
    sanitized = create_var_name(name, {}, 0)
    return sanitized or 'diagram'


def relation_statement(elements, relation):
    rel_name = getattr(relation, 'c4Description', '').replace("\n", " ")
    if not rel_name:
        rel_name = 'Вызов'
    rel_technology = getattr(relation, 'c4Technology', '').replace("\n", " ")
    if not rel_technology:
        rel_technology = 'unknown'
    return "    " + elements[relation.source][0] + " -> " + elements[relation.target][0] + ' "' + rel_name + '" "' + rel_technology + '"\n'


def build_names(components, file):
    names = list()
    visible_names = dict()
    dubles = dict()

    children_map = {}
    for comp in components.values():
        pid = comp.parent_id
        children_map.setdefault(pid, []).append(comp)

    visited = set()
    for comp in components.values():
        if comp.parent_id is None:
            recurse_walk(components, children_map, [], file, comp, 1,
                         names, visible_names, dubles, visited)
    return names


def export_to_hierarchical_dsl(components, relations):
    relationships_dir = Path('relationships')
    views_dir = Path('views')
    relationships_dir.mkdir(exist_ok=True)
    views_dir.mkdir(exist_ok=True)
    for output_dir in (relationships_dir, views_dir):
        for old_file in output_dir.glob('*.dsl'):
            old_file.unlink()

    with open('workspace.dsl', 'w', encoding='utf-8') as file:
        file.write('workspace {\n')
        file.write('model {\n')
        names = build_names(components, file)
        elements = {n[3]: n for n in names}

        system_relations = []
        container_relations_by_system = {}
        element_top_level = {}
        for element_id, element in components.items():
            current = element
            while current.parent_id is not None and current.parent_id in components:
                current = components[current.parent_id]
            element_top_level[element_id] = current.id

        for relation in relations:
            if relation.source not in elements or relation.target not in elements:
                rel_name = getattr(relation, 'c4Description', '').replace("\n", " ") or relation.id
                print(f'Предупреждение: пропуск связи "{rel_name}" — компонент не найден в модели')
                continue
            source_depth = elements[relation.source][1]
            target_depth = elements[relation.target][1]
            if source_depth == 1 and target_depth == 1:
                system_relations.append(relation)
            else:
                owner_id = element_top_level.get(relation.source)
                if source_depth == 1:
                    owner_id = element_top_level.get(relation.target)
                container_relations_by_system.setdefault(owner_id, []).append(relation)

        relationship_includes = []
        if system_relations:
            path = relationships_dir / 'system-context.dsl'
            with path.open('w', encoding='utf-8') as rel_file:
                for relation in system_relations:
                    rel_file.write(relation_statement(elements, relation))
            relationship_includes.append(path)

        for owner_id, owner_relations in container_relations_by_system.items():
            if owner_id not in elements:
                continue
            path = relationships_dir / f'container-{sanitize_file_name(elements[owner_id][0])}.dsl'
            with path.open('w', encoding='utf-8') as rel_file:
                for relation in owner_relations:
                    rel_file.write(relation_statement(elements, relation))
            relationship_includes.append(path)

        for path in relationship_includes:
            file.write(f'    !include {path.as_posix()}\n')

        file.write('}\n')
        file.write('views {\n')

        system_landscape_path = views_dir / 'system-landscape.dsl'
        with system_landscape_path.open('w', encoding='utf-8') as view_file:
            view_file.write('    systemLandscape {\n')
            view_file.write('        include *\n')
            view_file.write('        autoLayout\n')
            view_file.write('    }\n')
        file.write(f'    !include {system_landscape_path.as_posix()}\n')

        for n in names:
            if n[2] > 0:
                if n[1] == 1:
                    path = views_dir / f'container-{sanitize_file_name(n[0])}.dsl'
                    with path.open('w', encoding='utf-8') as view_file:
                        view_file.write(f'    container {n[0]} {{\n')
                        view_file.write('        include *\n')
                        view_file.write('        autoLayout\n')
                        view_file.write('    }\n')
                    file.write(f'    !include {path.as_posix()}\n')
                elif n[1] == 2:
                    path = views_dir / f'component-{sanitize_file_name(n[0])}.dsl'
                    with path.open('w', encoding='utf-8') as view_file:
                        view_file.write(f'    component {n[0]} {{\n')
                        view_file.write('        include *\n')
                        view_file.write('        autoLayout\n')
                        view_file.write('    }\n')
                    file.write(f'    !include {path.as_posix()}\n')

        file.write('    themes default\n')
        file.write('    }\n')
        file.write('}\n')

# main function
def main(argv):
    inputfiles = []
    check_data = False
    print_statistics = False
    hierarchical_output = False

    helpstring = 'drawio_parser.py -i <inputfile> [-i <inputfile> ...] [-d] [-s] [-H]'
    try:
        opts, args = getopt.getopt(argv, "sdhHi:", ["ifile=", "hierarchical"])
    except getopt.GetoptError:
        print(helpstring)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(helpstring)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfiles.append(arg)
        elif opt == '-d':
            check_data = True
        elif opt == '-s':
            print_statistics = True
        elif opt in ('-H', '--hierarchical'):
            hierarchical_output = True

    if len(inputfiles) == 0:
        print(helpstring)
        sys.exit()

    model_parts = [process_drawio_file(inputfile, print_statistics) for inputfile in inputfiles]
    if len(model_parts) == 1:
        components, relations = model_parts[0]
    else:
        components, relations = merge_models(model_parts)

    i = 1
    i = check_relations(components, relations, i, check_data)
    i = check_components(components, relations, i)

    if hierarchical_output:
        export_to_hierarchical_dsl(components, relations)
    else:
        export_to_dsl(components, relations)

    print_export_summary(components, relations)

if __name__ == "__main__":
   main(sys.argv[1:])
