package br.com.quinacampeao;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.Intent;
import android.net.Uri;
import android.graphics.*;
import android.graphics.pdf.PdfDocument;
import android.view.*;
import android.widget.*;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.*;
import java.util.*;

public class MainActivity extends Activity {
    private static final int PICK=1, SAVE=2;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView status;
    private Button start, export;
    private File input, resultDir, pdfFile;
    private int[] chosen;
    private int contests, lastContest, examined; private double score;
    private boolean running=false;
    private static final int[][] BLOCKS={
        {1,2,11,12,21,22,31,32},{3,4,13,14,23,24,33,34},{5,6,15,16,25,26,35,36},
        {7,8,17,18,27,28,37,38},{9,10,19,20,29,30,39,40},
        {41,42,51,52,61,62,71,72},{43,44,53,54,63,64,73,74},{45,46,55,56,65,66,75,76},
        {47,48,57,58,67,68,77,78},{49,50,59,60,69,70,79,80}};
    @Override public void onCreate(Bundle b){super.onCreate(b);
        if(!Python.isStarted()) Python.start(new AndroidPlatform(this));
        resultDir=new File(getFilesDir(),"RESULTADOS_QUINA_CAMPEAO_V1");resultDir.mkdirs();
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(24,30,24,20);
        root.setBackgroundColor(Color.rgb(247,242,253));
        TextView title=new TextView(this);title.setText("QUINA CAMPEAO V1");title.setTextSize(23);title.setTextColor(Color.rgb(111,36,162));root.addView(title);
        TextView sub=new TextView(this);sub.setText("Motor Windows V1 • 75 falhas • 10 blocos • 24.040.016 jogos");sub.setTextSize(13);root.addView(sub);
        start=new Button(this);start.setText("1. SELECIONAR HISTORICO TXT/CSV");root.addView(start);
        Button run=new Button(this);run.setText("2. ANALISAR TODOS OS CONCURSOS");root.addView(run);
        export=new Button(this);export.setText("3. SALVAR VOLANTE PDF");export.setEnabled(false);root.addView(export);
        ScrollView scroll=new ScrollView(this);status=new TextView(this);status.setTextSize(14);status.setTextIsSelectable(true);status.setText("Selecione o arquivo do historico para comecar.");scroll.addView(status);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        setContentView(root);
        start.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(i,PICK);});
        run.setOnClickListener(v->begin());
        export.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/pdf");i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_TITLE,"VOLANTE_QUINA_CAMPEAO_V1.pdf");startActivityForResult(i,SAVE);});
        handler.postDelayed(new Runnable(){public void run(){if(running){File log=new File(resultDir,"ANDAMENTO.txt");if(log.exists())try{byte[] data=read(log);String s=new String(data,"UTF-8");status.setText(s.length()>5500?s.substring(s.length()-5500):s);}catch(Exception ignored){}}handler.postDelayed(this,1500);}},1500);
    }
    @Override protected void onActivityResult(int req,int res,Intent data){super.onActivityResult(req,res,data);if(res!=RESULT_OK||data==null)return;
        if(req==PICK){try(InputStream in=getContentResolver().openInputStream(data.getData())){
            input=new File(getCacheDir(),"historico_quina.txt");try(FileOutputStream out=new FileOutputStream(input)){byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);}
            status.setText("Arquivo carregado: "+data.getData()+"\nPronto para analisar.");
        }catch(Exception e){status.setText("Erro ao abrir historico: "+e);}}
        if(req==SAVE&&pdfFile!=null){try(OutputStream out=getContentResolver().openOutputStream(data.getData());FileInputStream in=new FileInputStream(pdfFile)){
            byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);status.setText("PDF salvo com sucesso.\n"+data.getData());
        }catch(Exception e){status.setText("Erro ao salvar PDF: "+e);}}
    }
    private void begin(){if(running)return;if(input==null){status.setText("Primeiro selecione o historico.");return;}
        running=true;export.setEnabled(false);status.setText("Iniciando analise completa...\nPode demorar muito no celular. Mantenha o app aberto.");
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        new Thread(()->{try{
            String value=Python.getInstance().getModule("android_bridge").callAttr("run",input.getAbsolutePath(),resultDir.getAbsolutePath()).toString();
            String[] parts=value.split("\\|");String[] nums=parts[0].split(",");chosen=new int[5];for(int i=0;i<5;i++)chosen[i]=Integer.parseInt(nums[i]);
            contests=Integer.parseInt(parts[1]);lastContest=Integer.parseInt(parts[2]);examined=Integer.parseInt(parts[3]);score=Double.parseDouble(parts[4]);
            pdfFile=new File(resultDir,"VOLANTE_QUINA_CAMPEAO_V1.pdf");createPdf(pdfFile);
            handler.post(()->{running=false;getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);export.setEnabled(true);status.setText("CONCLUIDO!\nJogo: "+Arrays.toString(chosen)+"\nConcursos: "+contests+"\nJogos examinados: "+examined+"\nToque SALVAR VOLANTE PDF.");});
        }catch(Exception e){handler.post(()->{running=false;getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);status.setText("ERRO: "+e+"\nConfira seu TXT e tente novamente.");});}}).start();
    }
    private byte[] read(File f)throws IOException{try(FileInputStream in=new FileInputStream(f);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toByteArray();}}
    private void createPdf(File file)throws IOException{
        PdfDocument pdf=new PdfDocument();
        PdfDocument.PageInfo pi=new PdfDocument.PageInfo.Builder(595,842,1).create();
        PdfDocument.Page page=pdf.startPage(pi);
        Canvas c=page.getCanvas();Paint p=new Paint(3);c.drawColor(Color.WHITE);
        int purple=Color.rgb(111,36,162),green=Color.rgb(20,141,70),dark=Color.rgb(61,42,79);
        p.setColor(purple);c.drawRoundRect(35,38,560,104,10,10,p);
        p.setColor(Color.WHITE);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(26);center(c,p,"QUINA CAMPEAO",297,80);
        p.setColor(dark);p.setTextSize(13);center(c,p,"VOLANTE DIVIDIDO EM 10 BLOCOS",297,132);
        p.setTypeface(Typeface.DEFAULT);p.setTextSize(10);center(c,p,"10 blocos de 8 dezenas | 5 dezenas marcadas em verde",297,151);
        float left=35,bw=105,top=175,head=28,rowH=27,gh=head+4*rowH,gap=20;
        HashSet<Integer> marked=new HashSet<>();for(int x:chosen)marked.add(x);
        for(int band=0;band<2;band++)for(int col=0;col<5;col++){
            int id=band*5+col;float x=left+col*bw,y=top+band*(gh+gap);
            p.setColor(Color.rgb(250,248,253));p.setStyle(Paint.Style.FILL);c.drawRect(x,y,x+bw,y+gh,p);
            p.setColor(purple);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.5f);c.drawRect(x,y,x+bw,y+gh,p);p.setStyle(Paint.Style.FILL);
            c.drawRect(x,y,x+bw,y+head,p);p.setColor(Color.WHITE);p.setTextSize(10);p.setTypeface(Typeface.DEFAULT_BOLD);center(c,p,"BLOCO "+(id+1),x+bw/2,y+19);
            for(int j=0;j<8;j++){
                int n=BLOCKS[id][j];float cx=x+26+(j%2)*53,cy=y+head+rowH*((j/2)+.5f);
                p.setColor(marked.contains(n)?Color.rgb(226,243,232):Color.WHITE);c.drawCircle(cx,cy,12,p);
                p.setColor(marked.contains(n)?green:Color.rgb(211,203,223));p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(marked.contains(n)?2.5f:.65f);c.drawCircle(cx,cy,12,p);p.setStyle(Paint.Style.FILL);
                p.setColor(marked.contains(n)?green:dark);p.setTextSize(11);p.setTypeface(marked.contains(n)?Typeface.DEFAULT_BOLD:Typeface.DEFAULT);center(c,p,String.format(java.util.Locale.US,"%02d",n),cx,cy+4);
            }
        }
        float y=top+2*gh+gap+50;
        StringBuilder game=new StringBuilder();for(int n:chosen){if(game.length()>0)game.append(" - ");game.append(String.format(java.util.Locale.US,"%02d",n));}
        p.setColor(green);p.setTypeface(Typeface.DEFAULT_BOLD);p.setTextSize(21);center(c,p,game.toString(),297,y);
        p.setColor(dark);p.setTypeface(Typeface.DEFAULT);p.setTextSize(11);center(c,p,"Concursos: "+contests+" | Ultimo: "+lastContest+" | Jogos: "+examined,297,y+30);
        center(c,p,"Pontuacao: "+String.format(java.util.Locale.US,"%.3f",score),297,y+50);
        p.setTextSize(9);center(c,p,"Analise das 75 falhas, blocos e superposicoes.",297,y+75);
        p.setTextSize(8);center(c,p,"Classificacao historica nao aumenta a chance matematica de acerto.",297,803);
        center(c,p,"Volante de estudo - nao oficial.",297,818);
        pdf.finishPage(page);
        try(FileOutputStream out=new FileOutputStream(file)){pdf.writeTo(out);}finally{pdf.close();}
    }
    private void center(Canvas c,Paint p,String s,float x,float y){c.drawText(s,x-p.measureText(s)/2,y,p);}
}
