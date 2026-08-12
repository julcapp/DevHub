from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.indexer import ProjectIndexer
from app.knowledge import KnowledgeGraph


@dataclass(frozen=True)
class ModuleArchitecture:
    name: str
    path: str
    dependencies: tuple[str, ...]
    dependents: tuple[str, ...]
    symbols: tuple[str, ...]
    coupling: int = 0
    risk_score: int = 0
    risk_level: str = "Низкий"


@dataclass(frozen=True)
class ArchitectureSummary:
    project_name: str
    project_path: str
    files: int
    folders: int
    modules: int
    classes: int
    methods: int
    functions: int
    imports: int
    internal_dependencies: int
    nodes_total: int
    edges_total: int
    dependencies: tuple[str, ...]
    module_details: tuple[ModuleArchitecture, ...] = ()
    cycles: tuple[tuple[str, ...], ...] = ()
    warnings: tuple[str, ...] = ()
    top_risks: tuple[ModuleArchitecture, ...] = ()


class ArchitectureWorkspaceController:
    """Готовит архитектурную сводку, метрики модулей и предупреждения."""

    def __init__(self, indexer: ProjectIndexer | None = None) -> None:
        self.indexer = indexer or ProjectIndexer(); self.graph: KnowledgeGraph | None = None

    def analyze(self, root: Path) -> ArchitectureSummary:
        graph, result = self.indexer.build_graph(root); self.graph = graph
        counts: dict[str, int] = {}
        for node in graph.nodes: counts[node.kind] = counts.get(node.kind, 0) + 1
        dependencies: list[str] = []; adjacency: dict[str, set[str]] = {}; reverse: dict[str, set[str]] = {}
        modules = sorted((node for node in graph.nodes if node.kind == "Module"), key=lambda n: n.label)
        for module in modules: adjacency[module.label] = set(); reverse[module.label] = set()
        for edge in graph.edges:
            if edge.relation != "depends_on": continue
            source = graph.get_node(edge.source); target = graph.get_node(edge.target)
            if source and target:
                dependencies.append(f"{source.label} → {target.label}"); adjacency.setdefault(source.label,set()).add(target.label); adjacency.setdefault(target.label,set()); reverse.setdefault(target.label,set()).add(source.label); reverse.setdefault(source.label,set())
        cycles = self._find_cycles(adjacency); cycle_modules = {name for cycle in cycles for name in cycle}
        module_details: list[ModuleArchitecture] = []
        for module in modules:
            symbols=[]
            for edge in graph.edges:
                if edge.relation == "defines" and edge.source == module.id:
                    symbol=graph.get_node(edge.target)
                    if symbol and symbol.kind in {"Class","Method","Function"}: symbols.append(f"{symbol.kind}: {symbol.label}")
            outgoing=tuple(sorted(adjacency.get(module.label,set()))); incoming=tuple(sorted(reverse.get(module.label,set())))
            coupling=len(outgoing)+len(incoming); score=min(100, len(outgoing)*10 + len(incoming)*6 + (30 if module.label in cycle_modules else 0) + min(len(symbols),10)*2)
            level="Высокий" if score>=60 else ("Средний" if score>=30 else "Низкий")
            module_details.append(ModuleArchitecture(module.label,str(module.attributes.get("path","")),outgoing,incoming,tuple(sorted(symbols)),coupling,score,level))
        warnings=self._build_warnings(cycles,adjacency,module_details)
        top_risks=tuple(sorted(module_details,key=lambda x:(-x.risk_score,-x.coupling,x.name))[:5])
        return ArchitectureSummary(root.resolve().name,str(root.resolve()),result.files_indexed,result.folders_indexed,counts.get("Module",0),counts.get("Class",0),counts.get("Method",0),counts.get("Function",0),result.imports_indexed,result.internal_dependencies_resolved,result.nodes_total,result.edges_total,tuple(sorted(dependencies)),tuple(module_details),cycles,warnings,top_risks)

    @staticmethod
    def _find_cycles(adjacency: dict[str,set[str]]) -> tuple[tuple[str,...],...]:
        found:set[tuple[str,...]]=set()
        def canonical(cycle:list[str])->tuple[str,...]:
            body=cycle[:-1]; return min(tuple(body[i:]+body[:i]) for i in range(len(body)))
        def visit(start:str,current:str,path:list[str],seen:set[str])->None:
            for target in adjacency.get(current,set()):
                if target==start and len(path)>1: found.add(canonical(path+[start]))
                elif target not in seen and len(path)<len(adjacency): visit(start,target,path+[target],seen|{target})
        for node in sorted(adjacency): visit(node,node,[node],{node})
        return tuple(sorted(found))

    @staticmethod
    def _build_warnings(cycles:tuple[tuple[str,...],...], adjacency:dict[str,set[str]], details:list[ModuleArchitecture]) -> tuple[str,...]:
        warnings=[]
        for cycle in cycles: warnings.append(f"Циклическая зависимость: {' → '.join((*cycle,cycle[0]))}")
        for module,targets in sorted(adjacency.items()):
            if len(targets)>=5: warnings.append(f"Высокая связанность: {module} зависит от {len(targets)} внутренних модулей")
        for item in sorted(details,key=lambda x:x.risk_score,reverse=True):
            if item.risk_level=="Высокий": warnings.append(f"Высокий архитектурный риск: {item.name} — {item.risk_score}/100")
        return tuple(dict.fromkeys(warnings))
