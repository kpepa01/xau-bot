#property strict

// AUTO-MODULE ENGINE
// Creates missing module files at startup (safe/no overwrite if existing).

bool AME_FolderExists(const string folder)
{
   ResetLastError();
   long h = FileFindFirst(folder+"\\*",NULL,FILE_COMMON);
   if(h!=INVALID_HANDLE)
   {
      FileFindClose(h);
      return true;
   }
   // Try create as fallback (idempotent)
   ResetLastError();
   if(FolderCreate(folder,FILE_COMMON))
      return true;
   return (GetLastError()==ERR_DIRECTORY_EXISTS);
}

bool AME_WriteText(const string path,const string payload)
{
   int fh=FileOpen(path,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(fh==INVALID_HANDLE)
      return false;
   FileWriteString(fh,payload);
   FileClose(fh);
   return true;
}

string AME_AnalysisModuleTemplate()
{
   string s="";
   s+="#property strict\n";
   s+="enum RiskModeEnum { RISK_NORMAL=0, RISK_CAUTIOUS=1, RISK_BLOCKED=2 };\n";
   s+="struct AnalysisState { int TrendDirection; double TrendStrength; double StructureClarity; bool ChopDetected; string ATRMode; RiskModeEnum RiskMode; bool FakeBreakout; bool WickSpike; };\n";
   s+="double AM_iATR(string sym,ENUM_TIMEFRAMES tf,int p){return iATR(sym,tf,p);}\n";
   s+="double AM_EMA(string sym,ENUM_TIMEFRAMES tf,int p,int shift){return iMA(sym,tf,p,0,MODE_EMA,PRICE_CLOSE,shift);}\n";
   s+="bool AM_WickSpike(string sym,ENUM_TIMEFRAMES tf,int sh,double ratio){double o=iOpen(sym,tf,sh),c=iClose(sym,tf,sh),h=iHigh(sym,tf,sh),l=iLow(sym,tf,sh);double b=MathAbs(c-o);double uw=h-MathMax(o,c);double lw=MathMin(o,c)-l;return (b>0 && (uw/b>ratio || lw/b>ratio));}\n";
   s+="bool AM_FakeBreakout(string sym,ENUM_TIMEFRAMES tf,int sh){double h1=iHigh(sym,tf,sh+1),l1=iLow(sym,tf,sh+1),c0=iClose(sym,tf,sh),h0=iHigh(sym,tf,sh),l0=iLow(sym,tf,sh);if(h0>h1 && c0<h1) return true; if(l0<l1 && c0>l1) return true; return false;}\n";
   s+="void RunAnalysisModule(string sym,AnalysisState &st){double eH4f=AM_EMA(sym,PERIOD_H4,20,0),eH4s=AM_EMA(sym,PERIOD_H4,50,0);double eH1f=AM_EMA(sym,PERIOD_H1,20,0),eH1s=AM_EMA(sym,PERIOD_H1,50,0);double atrH1=AM_iATR(sym,PERIOD_H1,14);double atrM15=AM_iATR(sym,PERIOD_M15,14);st.TrendDirection=(eH4f>eH4s && eH1f>eH1s)?1:((eH4f<eH4s && eH1f<eH1s)?-1:0);st.TrendStrength=MathMin(100.0,MathAbs(eH1f-eH1s)/_Point);st.StructureClarity=MathMin(100.0,MathAbs(iClose(sym,PERIOD_H1,0)-iOpen(sym,PERIOD_H1,0))/MathMax(_Point,atrH1)*100.0);st.ChopDetected=(MathAbs(eH1f-eH1s) < atrH1*0.15);st.ATRMode=(atrM15>atrH1?\"EXPANDED\":\"NORMAL\");st.FakeBreakout=AM_FakeBreakout(sym,PERIOD_M15,0);st.WickSpike=AM_WickSpike(sym,PERIOD_M15,0,1.2);if(st.ChopDetected || st.WickSpike) st.RiskMode=RISK_CAUTIOUS; else st.RiskMode=RISK_NORMAL; if(st.FakeBreakout) st.RiskMode=RISK_BLOCKED;}\n";
   return s;
}

string AME_VisualPanelTemplate()
{
   string s="";
   s+="#property strict\n";
   s+="void VP_DrawHLine(string name,double price,color clr){if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_HLINE,0,0,price); ObjectSetDouble(0,name,OBJPROP_PRICE,price); ObjectSetInteger(0,name,OBJPROP_COLOR,clr);}\n";
   s+="void VP_DrawArrow(string name,datetime t,double p,bool buy){if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_ARROW,0,t,p); ObjectSetInteger(0,name,OBJPROP_ARROWCODE,buy?233:234); ObjectSetInteger(0,name,OBJPROP_COLOR,buy?clrLime:clrTomato); ObjectMove(0,name,0,t,p);}\n";
   s+="void VP_DrawRect(string name,datetime t1,double p1,datetime t2,double p2,color clr){if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_RECTANGLE,0,t1,p1,t2,p2); ObjectSetInteger(0,name,OBJPROP_COLOR,clr); ObjectSetInteger(0,name,OBJPROP_BACK,true); ObjectMove(0,name,0,t1,p1); ObjectMove(0,name,1,t2,p2);}\n";
   s+="void VP_UpdatePanel(string h4Trend,string h1Structure,string volMode,string atrMode,string newsMode,string riskMode){string n=\"VP_STATUS\";string txt=\"H4 Trend: \"+h4Trend+\"\\nH1 Structure: \"+h1Structure+\"\\nVolatility: \"+volMode+\"\\nATR Mode: \"+atrMode+\"\\nNews: \"+newsMode+\"\\nRisk: \"+riskMode; if(ObjectFind(0,n)<0) ObjectCreate(0,n,OBJ_LABEL,0,0,0); ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER); ObjectSetInteger(0,n,OBJPROP_XDISTANCE,10); ObjectSetInteger(0,n,OBJPROP_YDISTANCE,20); ObjectSetInteger(0,n,OBJPROP_COLOR,clrWhite); ObjectSetString(0,n,OBJPROP_TEXT,txt);}\n";
   return s;
}

string AME_NightReviewTemplate()
{
   string s="";
   s+="#property strict\n";
   s+="struct NightReviewState { string AvoidHours; string AvoidPatterns; string RiskModeNextDay; };\n";
   s+="bool NR_IsWindow(){MqlDateTime t; TimeToStruct(TimeCurrent(),t); return (t.hour>=22 || t.hour<0);}\n";
   s+="void NR_DrawMark(string name,datetime tm,double price,bool win){if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_TEXT,0,tm,price); ObjectSetString(0,name,OBJPROP_TEXT,win?\"✓\":\"X\"); ObjectSetInteger(0,name,OBJPROP_COLOR,win?clrLime:clrTomato);}\n";
   s+="void RunNightReview(NightReviewState &st){if(!NR_IsWindow()) return; datetime from=(datetime)(TimeCurrent()-86400); datetime to=TimeCurrent(); HistorySelect(from,to); int total=HistoryDealsTotal(); int wins=0,losses=0; for(int i=0;i<total;i++){ulong tk=HistoryDealGetTicket(i); if(tk==0) continue; double pr=HistoryDealGetDouble(tk,DEAL_PROFIT); datetime tm=(datetime)HistoryDealGetInteger(tk,DEAL_TIME); double px=HistoryDealGetDouble(tk,DEAL_PRICE); bool win=(pr>=0); if(win) wins++; else losses++; NR_DrawMark(\"NR_\"+(string)tk,tm,px,win);} st.AvoidHours=(losses>wins?\"13,14,15\":\"\"); st.AvoidPatterns=(losses>wins?\"wick_spike,fakeout\":\"\"); st.RiskModeNextDay=(losses>wins?\"Cautious\":\"Normal\");}\n";
   return s;
}

bool EnsureAutoModules()
{
   string base="modules";
   if(!AME_FolderExists(base))
      return false;

   string f1=base+"\\AnalysisModule.mqh";
   string f2=base+"\\VisualPanel.mqh";
   string f3=base+"\\NightReview.mqh";

   if(!FileIsExist(f1,FILE_COMMON)) if(!AME_WriteText(f1,AME_AnalysisModuleTemplate())) return false;
   if(!FileIsExist(f2,FILE_COMMON)) if(!AME_WriteText(f2,AME_VisualPanelTemplate())) return false;
   if(!FileIsExist(f3,FILE_COMMON)) if(!AME_WriteText(f3,AME_NightReviewTemplate())) return false;
   return true;
}
