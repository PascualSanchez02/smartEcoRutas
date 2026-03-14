from __future__ import annotations

import random
import time
from typing import List, Optional


def solve(problem, time_limit_s: float, seed: int | None = None) -> List[List[str]]:
    """
    Baseline robusto + mejora post-construcción para SmartEcoRutas.

    Estrategia:
      1) Construcción greedy por rutas (baseline original).
      2) Fase de mejora: intentar eliminar rutas mediante:
         - reassignment factible de contenedores entre rutas,
         - intentos de merge directo de secuencias de rutas.
      3) Siempre mantener fallback válido y respetar límite de tiempo.
    """
    t0 = time.time()
    rng = random.Random(0 if seed is None else int(seed))

    base = problem.base_uid()
    dump = problem.dump_uid()
    cap = int(problem.max_containers_before_dump)
    route_max = float(problem.route_max_work_s)
    svc_c = float(problem.service_time_container_s)
    svc_d = float(problem.service_time_dump_s)

    containers = list(problem.containers_uids())
    if not containers:
        return [[base, dump, base]]

    all_containers = set(containers)
    unvisited = set(containers)

    soft_deadline = t0 + 0.93 * max(0.0, float(time_limit_s))
    hard_deadline = t0 + max(0.0, float(time_limit_s))

    def near_limit() -> bool:
        return time.time() >= soft_deadline

    def hard_limit() -> bool:
        return time.time() >= hard_deadline

    def close_tail_s(cur_uid: str) -> float:
        return float(problem.time_uid(cur_uid, dump)) + svc_d + float(problem.time_uid(dump, base))

    def can_visit_and_close(cur_uid: str, nxt_uid: str, elapsed_s: float) -> bool:
        projected = elapsed_s + float(problem.time_uid(cur_uid, nxt_uid)) + svc_c
        return projected + close_tail_s(nxt_uid) <= route_max + 1e-9

    def can_go_dump_and_close(cur_uid: str, elapsed_s: float) -> bool:
        to_dump = float(problem.time_uid(cur_uid, dump)) + svc_d
        return elapsed_s + to_dump + float(problem.time_uid(dump, base)) <= route_max + 1e-9

    def nearest_feasible(cur_uid: str, elapsed_s: float) -> Optional[str]:
        if not unvisited:
            return None
        exclude = all_containers - unvisited
        k = min(96, len(unvisited))
        candidates = problem.k_nearest(cur_uid, k, only_containers=True, exclude=exclude)

        best_uid = None
        best_score = float("inf")
        for uid, travel_s in candidates:
            if uid not in unvisited:
                continue
            if not can_visit_and_close(cur_uid, uid, elapsed_s):
                continue
            if float(travel_s) < best_score:
                best_score = float(travel_s)
                best_uid = uid
        return best_uid

    def extract_containers(route: List[str]) -> List[str]:
        return [u for u in route if u in all_containers]

    # Cache de reconstrucciones para evitar recomputar build/travel muchas veces.
    eval_cache: dict[tuple[str, ...], tuple[Optional[List[str]], float]] = {}

    def build_route_from_sequence(seq: List[str]) -> Optional[List[str]]:
        if not seq:
            return [base, dump, base]

        route = [base]
        cur = base
        elapsed = 0.0
        load = 0

        for c in seq:
            if load >= cap:
                to_dump = float(problem.time_uid(cur, dump)) + svc_d
                elapsed += to_dump
                route.append(dump)
                cur = dump
                load = 0

            if not can_visit_and_close(cur, c, elapsed):
                if cur != dump:
                    to_dump = float(problem.time_uid(cur, dump)) + svc_d
                    if elapsed + to_dump + float(problem.time_uid(dump, c)) + svc_c + close_tail_s(c) <= route_max + 1e-9:
                        elapsed += to_dump
                        route.append(dump)
                        cur = dump
                        load = 0
                    else:
                        return None
                else:
                    return None

            elapsed += float(problem.time_uid(cur, c)) + svc_c
            route.append(c)
            cur = c
            load += 1

        if route[-1] != dump:
            elapsed += float(problem.time_uid(cur, dump)) + svc_d
            route.append(dump)
        if route[-1] != base:
            elapsed += float(problem.time_uid(dump, base))
            route.append(base)

        if elapsed > route_max + 1e-9:
            return None
        return route

    def eval_sequence(seq: List[str]) -> tuple[Optional[List[str]], float]:
        key = tuple(seq)
        cached = eval_cache.get(key)
        if cached is not None:
            return cached
        route = build_route_from_sequence(seq)
        travel = float(problem.travel_time_route_uids(route)) if route is not None else float("inf")
        eval_cache[key] = (route, travel)
        return route, travel

    def route_is_feasible(route: List[str]) -> bool:
        if len(route) < 3:
            return False
        if route[0] != base or route[-1] != base or route[-2] != dump:
            return False
        if problem.total_time_route_uids(route) > route_max + 1e-9:
            return False

        cnt = 0
        for u in route:
            if u == dump:
                cnt = 0
            elif u in all_containers:
                cnt += 1
                if cnt > cap:
                    return False
        return True

    routes: List[List[str]] = []

    while unvisited and not hard_limit():
        route = [base]
        cur = base
        elapsed = 0.0
        load = 0
        collected = 0

        while unvisited and not near_limit():
            if load >= cap:
                if not can_go_dump_and_close(cur, elapsed):
                    break
                route.append(dump)
                elapsed += float(problem.time_uid(cur, dump)) + svc_d
                cur = dump
                load = 0
                continue

            nxt = nearest_feasible(cur, elapsed)
            if nxt is None:
                break

            route.append(nxt)
            elapsed += float(problem.time_uid(cur, nxt)) + svc_c
            cur = nxt
            load += 1
            collected += 1
            unvisited.remove(nxt)

        if collected == 0 and unvisited:
            pick = min(unvisited, key=lambda u: problem.time_uid(base, u))
            route = [base, pick]
            unvisited.remove(pick)

        if route[-1] != dump:
            route.append(dump)
        if route[-1] != base:
            route.append(base)

        if route_is_feasible(route):
            routes.append(route)
        else:
            moved = [u for u in route if u in all_containers]
            for u in moved:
                routes.append([base, u, dump, base])

    if unvisited:
        rest = list(unvisited)
        rng.shuffle(rest)
        for u in rest:
            routes.append([base, u, dump, base])

    best_valid_routes = [list(r) for r in routes]

    route_seqs: List[List[str]] = [extract_containers(r) for r in routes]


    def _proxy_route_distance(seq: List[str], c: str) -> float:
        """Cheap proxy: distance from container c to sampled nodes of seq."""
        if not seq:
            return float(problem.time_uid(base, c))
        n = len(seq)
        if n <= 6:
            sample_idx = range(n)
        else:
            sample_idx = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1})
        best = float("inf")
        for i in sample_idx:
            t = float(problem.time_uid(seq[int(i)], c))
            if t < best:
                best = t
        return best

    def try_insert_container(target_seq: List[str], c: str, max_positions: int = 28) -> tuple[Optional[List[str]], float]:
        if not target_seq:
            cand = [c]
            _, travel = eval_sequence(cand)
            if travel == float("inf"):
                return None, float("inf")
            return cand, travel

        n = len(target_seq)
        if n + 1 <= max_positions:
            positions = range(n + 1)
        else:
            anchor = min(range(n), key=lambda i: problem.time_uid(target_seq[i], c))
            s = max(0, anchor - 6)
            e = min(n, anchor + 6)
            positions = sorted({0, n, s, e} | set(range(s, e + 1)))

        best_seq = None
        best_cost = float("inf")
        for pos in positions:
            cand = target_seq[:pos] + [c] + target_seq[pos:]
            _, travel = eval_sequence(cand)
            if travel < best_cost:
                best_cost = travel
                best_seq = cand

        return best_seq, best_cost

    ordered_idx = sorted(range(len(route_seqs)), key=lambda i: len(route_seqs[i]))

    for src in ordered_idx:
        if near_limit() or src >= len(route_seqs):
            break
        if not route_seqs[src]:
            continue

        source_conts = list(route_seqs[src])
        working = [list(s) for s in route_seqs]
        success = True

        merged_done = False
        for dst in sorted(range(len(working)), key=lambda i: len(working[i]), reverse=True):
            if dst == src or not working[dst]:
                continue
            cand_seq = working[dst] + source_conts
            cand_route, _ = eval_sequence(cand_seq)
            if cand_route is not None:
                working[dst] = cand_seq
                working[src] = []
                merged_done = True
                break

            cand_seq_rev = source_conts + working[dst]
            cand_route_rev, _ = eval_sequence(cand_seq_rev)
            if cand_route_rev is not None:
                working[dst] = cand_seq_rev
                working[src] = []
                merged_done = True
                break

        if not merged_done:
            for c in source_conts:
                if near_limit():
                    success = False
                    break

                best_dst = None
                best_seq = None
                best_delta = float("inf")

                dst_candidates = []
                for dst in range(len(working)):
                    if dst == src:
                        continue
                    proxy = _proxy_route_distance(working[dst], c)
                    dst_candidates.append((proxy, dst))

                dst_candidates.sort(key=lambda x: x[0])
                if len(source_conts) <= 4:
                    cand_dsts = [d for _, d in dst_candidates]
                else:
                    top_k = min(len(dst_candidates), 18)
                    cand_dsts = [d for _, d in dst_candidates[:top_k]]

                for dst in cand_dsts:
                    cur_dst_seq = working[dst]
                    _, old_travel = eval_sequence(cur_dst_seq)
                    if old_travel == float("inf"):
                        continue

                    cand_seq, cand_travel = try_insert_container(cur_dst_seq, c)
                    if cand_seq is None:
                        continue

                    delta = cand_travel - old_travel
                    if delta < best_delta:
                        best_delta = delta
                        best_dst = dst
                        best_seq = cand_seq

                if best_dst is None or best_seq is None:
                    success = False
                    break

                working[best_dst] = best_seq

            if success:
                working[src] = []

        if success:
            new_seqs = [s for s in working if s]
            if len(new_seqs) < len(route_seqs):
                rebuilt = []
                feasible_all = True
                for seq in new_seqs:
                    rr, _ = eval_sequence(seq)
                    if rr is None or not route_is_feasible(rr):
                        feasible_all = False
                        break
                    rebuilt.append(rr)

                if feasible_all:
                    route_seqs = new_seqs
                    routes = rebuilt
                    best_valid_routes = [list(r) for r in routes]

    seen = []
    final_ok = True
    for r in routes:
        if not route_is_feasible(r):
            final_ok = False
            break
        seen.extend([u for u in r if u in all_containers])

    if final_ok and len(seen) == len(containers) and len(set(seen)) == len(containers):
        return routes

    return best_valid_routes
