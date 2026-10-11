# -*- coding: utf-8 -*-
"""QUINA CAMPEAO V1 - estudo completo antes da busca exaustiva."""
import collections
import itertools
import math
import os
import re
import sys
import time
from pathlib import Path

BLOCKS = [tuple(row * 10 + col + 1 for row in range(base, base + 4) for col in (2 * pair, 2 * pair + 1)) for base in (0, 4) for pair in range(5)]
NUMBER_BLOCK = {n: i for i, block in enumerate(BLOCKS) for n in block}
NUMBER_ROW = {n: (n - 1) // 10 for n in range(1, 81)}
WINDOWS = (10, 20, 50, 100, 200)
TOTAL = math.comb(80, 5)


def pick_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        selected = filedialog.askopenfilename(title='Selecione o historico da QUINA', filetypes=[('Historico', '*.txt *.csv'), ('Todos', '*.*')])
        root.destroy()
        if selected: return Path(selected)
    except Exception as exc:
        print('Seletor de arquivos indisponivel:', exc, flush=True)
    entered = input('Caminho completo do TXT/CSV: ').strip().strip('"')
    if not entered: raise RuntimeError('Nenhum arquivo selecionado')
    return Path(entered)


def decode_file(path):
    raw = path.read_bytes()
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode('utf-8', errors='replace')


def parse_history(path):
    rows, errors = {}, []
    for line_no, line in enumerate(decode_file(path).splitlines(), 1):
        line = line.strip()
        if not line: continue
        # Supports "concurso - 01 02 03 04 05", semicolon CSV and tabs.
        # A date between contest and balls is ignored.
        normalized = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', ' ', line)
        normalized = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' ', normalized)
        tokens = re.findall(r'\d+', normalized)
        if len(tokens) < 5:
            if line_no > 2 or re.search(r'\d', line): errors.append((line_no, 'sem cinco dezenas', line[:110]))
            continue
        # Five rightmost numeric fields represent the balls.
        vals = list(map(int, tokens[-5:]))
        if len(set(vals)) != 5 or not all(1 <= x <= 80 for x in vals):
            errors.append((line_no, 'dezenas invalidas', line[:110])); continue
        # Contest id from prefix (if present). Header without contest uses sequential index.
        prefix = tokens[:-5]
        contest = int(prefix[0]) if prefix else len(rows) + 1
        if contest <= 0:
            errors.append((line_no, 'concurso invalido', line[:110])); continue
        if contest in rows:
            if rows[contest] != tuple(sorted(vals)):
                errors.append((line_no, 'concurso duplicado divergente', line[:110]))
            continue
        rows[contest] = tuple(sorted(vals))
    if len(rows) < 10: raise RuntimeError('Apenas %d concursos validos. Confira o formato do arquivo. Exemplo: 1 - 04 12 25 51 70' % len(rows))
    ids = sorted(rows)
    gaps = [(a + 1, b - 1) for a, b in zip(ids, ids[1:]) if b > a + 1]
    return [(i, rows[i]) for i in ids], errors, gaps


def signature(nums):
    blocks = [0] * 10
    for n in nums: blocks[NUMBER_BLOCK[n]] += 1
    gaps = [b - a for a, b in zip(nums, nums[1:])]
    return (sum(n % 2 for n in nums), sum(nums) // 20, sum(x > 1 for x in blocks), max(blocks), sum(g == 1 for g in gaps), sum(g >= 15 for g in gaps))


def study(history):
    draws = [set(x) for _, x in history]
    last = draws[-1]
    absence_masks = [((1 << 80) - 1) ^ sum(1 << (n - 1) for n in d) for d in draws]
    n = len(draws)
    fail = [0] * 81; present = [0] * 81; recent = {}
    for d in draws:
        for x in range(1, 81):
            if x in d: present[x] += 1
            else: fail[x] += 1
    streak = [0] * 81
    for x in range(1, 81):
        for d in reversed(draws):
            if x in d: break
            streak[x] += 1
    for w in WINDOWS:
        part = draws[-min(w, n):]
        recent[w] = {x: sum(x not in d for d in part) / len(part) for x in range(1, 81)}
    overlaps = collections.Counter()
    # Compare every historical pair. For 75-absence sets, overlap is always >=70/75 = 93.33%.
    print('ETAPA 2/5: comparando todas as superposicoes de 75 falhas...', flush=True)
    for i, a in enumerate(absence_masks):
        for b in absence_masks[:i]: overlaps[(a & b).bit_count()] += 1
        if (i + 1) % 500 == 0: print('  Superposicoes: %d/%d concursos' % (i + 1, n), flush=True)
    repeats = collections.Counter(len(a & b) for a, b in zip(draws, draws[1:]))
    sig_counts = collections.Counter(signature(tuple(sorted(d))) for d in draws)
    pair_counts = collections.Counter()
    block_miss = [0] * 10
    block_miss_recent = [0] * 10
    block_pair_miss = collections.Counter()
    for j, d in enumerate(draws):
        for a, b in itertools.combinations(sorted(d), 2): pair_counts[(a, b)] += 1
        missing = [k for k, block in enumerate(BLOCKS) if not (set(block) & d)]
        for k in missing:
            block_miss[k] += 1
            if j >= n - min(50, n): block_miss_recent[k] += 1
        for a, b in itertools.combinations(missing, 2): block_pair_miss[(a, b)] += 1
    # Predominant and growing failures are quantified, not assumed to be predictive.
    weights = [0.0] * 81
    for x in range(1, 81):
        baseline = fail[x] / n
        growth = recent[20][x] - recent[100][x]
        # Penalize excessive streaks mildly; no gambler's fallacy assertion.
        weights[x] = 0.55 * (1 - baseline) + 0.25 * growth + 0.20 * min(streak[x], 30) / 30
    return locals()


def audit(st, history, errors, gaps, path):
    lines = ['QUINA CAMPEAO V1 - AUDITORIA ANTES DO JOGO', '=' * 70,
             'Arquivo: ' + str(path), 'Concursos validos: %d' % len(history),
             'Primeiro: %d | Ultimo: %d' % (history[0][0], history[-1][0]),
             'Ultimo sorteio: ' + ' '.join('%02d' % x for x in history[-1][1]),
             'Linhas rejeitadas: %d' % len(errors), 'Lacunas na numeracao: %d' % len(gaps), '',
             'SUPERPOSICAO DAS 75 FALHAS (pares de concursos):']
    lines += ['%d dezenas em comum (%.2f%%): %d pares' % (k, k / 75 * 100, v) for k, v in sorted(st['overlaps'].items())]
    lines += ['', 'REPETIDAS DO CONCURSO ANTERIOR:']
    lines += ['%d repetidas: %d vezes' % (k, st['repeats'][k]) for k in range(6)]
    lines += ['', 'BLOCOS (2 COLUNAS X 4 LINHAS):']
    for i, block in enumerate(BLOCKS):
        lines.append('B%02d %s | ausente inteiro: %d concursos | ultimos 50: %d' %
                     (i + 1, ' '.join('%02d' % x for x in block), st['block_miss'][i], st['block_miss_recent'][i]))
    lines += ['', 'PARES DE BLOCOS MAIS AUSENTES:']
    for (a, b), ct in st['block_pair_miss'].most_common(20): lines.append('B%02d + B%02d: %d' % (a + 1, b + 1, ct))
    lines += ['', 'FALHAS POR DEZENA: total, sequencia atual, recortes 20/50/100:']
    for x in range(1, 81):
        lines.append('%02d | total=%d | sequencia=%d | 20=%.1f%% | 50=%.1f%% | 100=%.1f%% | crescimento20-100=%+.1f pp' %
                     (x, st['fail'][x], st['streak'][x], st['recent'][20][x]*100,
                      st['recent'][50][x]*100, st['recent'][100][x]*100,
                      (st['recent'][20][x] - st['recent'][100][x])*100))
    lines += ['', 'PADROES HISTORICOS MAIS COMUNS (impares, faixa soma, blocos ocupados, max por bloco, adjacentes, saltos grandes):']
    lines += ['%s: %d concursos' % (str(k), v) for k, v in st['sig_counts'].most_common(30)]
    lines += ['', 'LINHAS REJEITADAS (ate 100):']
    lines += ['Linha %d: %s | %s' % item for item in errors[:100]]
    lines += ['', 'LACUNAS (ate 100):', *[str(g) for g in gaps[:100]]]
    return '\n'.join(lines) + '\n'


def choose(st, history, output):
    last = set(history[-1][1]); weights = st['weights']; sigcounts = st['sig_counts']; paircounts = st['pair_counts']
    total_hist = len(history)
    best = None; bestscore = -1e100; eligible = 0; started = time.monotonic()
    # Enumerate ALL C(80,5) games. Only 1-repeat games are eligible for the winner.
    print('ETAPA 4/5: avaliando TODAS as %s combinacoes...' % f'{TOTAL:,}'.replace(',', '.'), flush=True)
    for idx, game in enumerate(itertools.combinations(range(1, 81), 5), 1):
        if len(last.intersection(game)) == 1:
            eligible += 1
            sig = signature(game)
            occupied = sig[2]
            # Favor historical structural patterns, then joint pairs and failure signals.
            historical = math.log1p(sigcounts.get(sig, 0))
            pairs = sum(paircounts.get((a, b), 0) for a, b in itertools.combinations(game, 2)) / total_hist
            block_pattern = len({NUMBER_BLOCK[x] for x in game})
            score = 5.0 * historical + 2.0 * pairs + sum(weights[x] for x in game) + 0.1 * block_pattern
            if score > bestscore: bestscore, best = score, game
        if idx % 500000 == 0 or idx == TOTAL:
            pct = idx * 100 / TOTAL
            print('  %s / %s | %5.1f%% | elegiveis %s | tempo %.0fs | melhor %s' %
                  (f'{idx:,}'.replace(',', '.'), f'{TOTAL:,}'.replace(',', '.'), pct,
                   f'{eligible:,}'.replace(',', '.'), time.monotonic() - started,
                   ' '.join('%02d' % x for x in best) if best else '-'), flush=True)
    if best is None: raise RuntimeError('Nenhum jogo elegivel')
    return best, bestscore, eligible


def make_pdf(path, game, history, score):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    c = canvas.Canvas(str(path), pagesize=A4); W, H = A4
    c.setFillColorRGB(0.97, 0.97, 0.96); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColorRGB(0.92, 0.48, 0.10); c.roundRect(34, H - 115, W - 68, 72, 12, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1); c.setFont('Helvetica-Bold', 25); c.drawCentredString(W / 2, H - 85, 'QUINA CAMPEAO V1')
    c.setFillColorRGB(0.2, 0.25, 0.29); c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(W / 2, H - 140, 'VOLANTE - 10 BLOCOS DE 8 DEZENAS')
    c.setFont('Helvetica', 10); c.drawCentredString(W / 2, H - 157, '5 blocos superiores + 5 inferiores | marcacoes verdes')
    left, gap, bw, bh = 30, 6, (W - 60 - 4 * 6) / 5, 220
    for bi, block in enumerate(BLOCKS):
        r, col = divmod(bi, 5); x = left + col * (bw + gap); top = H - 183 - r * (bh + 20)
        c.setStrokeColorRGB(0.13, 0.47, 0.72); c.setLineWidth(1.5); c.rect(x, top - bh, bw, bh, stroke=1, fill=0)
        c.setFillColorRGB(0.13, 0.47, 0.72); c.rect(x, top - 29, bw, 29, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1); c.setFont('Helvetica-Bold', 10); c.drawCentredString(x + bw / 2, top - 19, 'BLOCO %d' % (bi + 1))
        for pos, number in enumerate(block):
            rr, cc = divmod(pos, 2); cx = x + bw * (0.28 if cc == 0 else 0.72); cy = top - 52 - rr * 43
            c.setLineWidth(0.7); c.setStrokeColorRGB(0.76, 0.80, 0.81); c.circle(cx, cy, 16, stroke=1, fill=0)
            if number in game:
                c.setStrokeColorRGB(0.05, 0.58, 0.25); c.setLineWidth(3); c.circle(cx, cy, 19, stroke=1, fill=0)
            c.setFillColorRGB(0.12, 0.2, 0.2); c.setFont('Helvetica-Bold', 12); c.drawCentredString(cx, cy - 4, '%02d' % number)
    c.setFillColorRGB(0.16, 0.2, 0.23); c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(W / 2, 115, 'JOGO ESCOLHIDO: ' + '  '.join('%02d' % x for x in game))
    c.setFont('Helvetica', 9); c.drawCentredString(W / 2, 95, 'Historico: %d concursos | Ultimo: %d | Pontuacao: %.3f' % (len(history), history[-1][0], score))
    c.setFont('Helvetica', 8); c.drawCentredString(W / 2, 70, 'Metodo de classificacao historica. Nao aumenta a chance matematica de acerto.')
    c.save()


def main():
    print('\nQUINA CAMPEAO V1 - FALHAS E SUPERPOSICOES\n', flush=True)
    path = pick_file()
    print('ETAPA 1/5: lendo e validando todos os concursos...', flush=True)
    history, errors, gaps = parse_history(path)
    print('Concursos: %d | rejeitadas: %d | lacunas: %d | ultimo: %d' %
          (len(history), len(errors), len(gaps), history[-1][0]), flush=True)
    st = study(history)
    output = Path(__file__).resolve().parent / 'RESULTADOS_QUINA_CAMPEAO_V1'; output.mkdir(exist_ok=True)
    print('ETAPA 3/5: salvando AUDITORIA ANTES de escolher o jogo...', flush=True)
    (output / 'AUDITORIA_ANTES_DO_JOGO_V1.txt').write_text(audit(st, history, errors, gaps, path), encoding='utf-8')
    print('Auditoria salva!', flush=True)
    game, score, eligible = choose(st, history, output)
    print('ETAPA 5/5: gerando o PDF e o resumo...', flush=True)
    make_pdf(output / 'VOLANTE_QUINA_CAMPEAO_V1.pdf', game, history, score)
    summary = 'QUINA CAMPEAO V1\nJogo: %s\nUltimo concurso: %d\nRepetida: %s\nJogos totais: %d\nElegiveis: %d\nPontuacao: %.5f\n' % (
        ' '.join('%02d' % x for x in game), history[-1][0],
        ' '.join('%02d' % x for x in set(game) & set(history[-1][1])), TOTAL, eligible, score)
    (output / 'JOGO_ESCOLHIDO_V1.txt').write_text(summary, encoding='utf-8')
    print('\n' + summary + '\nPDF e relatorios em: ' + str(output), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        input('\nERRO. Pressione ENTER para sair...')
        sys.exit(1)
