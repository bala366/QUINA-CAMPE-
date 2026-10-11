# Adapter Android: chama diretamente o motor Windows da Quina Campeao V1.
import contextlib
from pathlib import Path
import quina_campeao_v1 as motor

class Progress:
    def __init__(self,path): self.path=Path(path)
    def write(self,s):
        if s:
            with self.path.open('a',encoding='utf-8') as f: f.write(s)
    def flush(self): pass

def run(history_file,output_dir):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    log=out/'ANDAMENTO.txt';log.write_text('QUINA CAMPEAO V1\n',encoding='utf-8')
    with contextlib.redirect_stdout(Progress(log)):
        print('ETAPA 1/5: lendo historico...',flush=True)
        history,errors,gaps=motor.parse_history(Path(history_file))
        print('Concursos validos:',len(history),'| rejeitadas:',len(errors),'| lacunas:',len(gaps),flush=True)
        print('ETAPA 2/5: estudando falhas e superposicoes...',flush=True)
        stats=motor.study(history)
        print('ETAPA 3/5: salvando auditoria...',flush=True)
        (out/'AUDITORIA_ANTES_DO_JOGO_V1.txt').write_text(motor.audit(stats,history,errors,gaps,history_file),encoding='utf-8')
        print('ETAPA 4/5: analisando 24.040.016 combinacoes...',flush=True)
        game,score,eligible=motor.choose(stats,history,out)
        summary=('QUINA CAMPEAO V1\nJogo: '+' '.join('%02d'%x for x in game)+
                 '\nConcursos: '+str(len(history))+'\nUltimo: '+str(history[-1][0])+
                 '\nElegiveis: '+str(eligible)+'\nPontuacao: '+str(score)+'\n')
        (out/'JOGO_ESCOLHIDO_V1.txt').write_text(summary,encoding='utf-8')
        print('ETAPA 5/5: jogo escolhido:',game,'pontuacao:',score,flush=True)
        return ','.join(map(str,game))+'|'+str(len(history))+'|'+str(history[-1][0])+'|'+str(motor.TOTAL)+'|'+str(score)
