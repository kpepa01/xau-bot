#property strict

struct NightReviewState {
   string AvoidHours;
   string AvoidPatterns;
   string RiskModeNextDay;
};

bool NR_IsActiveWindow()
{
   MqlDateTime t; TimeToStruct(TimeCurrent(),t);
   return (t.hour>=22 || t.hour<0);
}

void NR_DrawTradeMark(const ulong ticket,const datetime tm,const double price,const bool win)
{
   string n="NR_MARK_"+(string)ticket;
   if(ObjectFind(0,n)<0) ObjectCreate(0,n,OBJ_TEXT,0,tm,price);
   ObjectSetString(0,n,OBJPROP_TEXT,win?"✓":"X");
   ObjectSetInteger(0,n,OBJPROP_COLOR,win?clrLime:clrTomato);
}

void RunNightReview(NightReviewState &state)
{
   if(!NR_IsActiveWindow()) return;

   datetime from=(datetime)(TimeCurrent()-86400);
   datetime to=TimeCurrent();
   HistorySelect(from,to);

   int wins=0,losses=0;
   int dangerousHourCount[24]; ArrayInitialize(dangerousHourCount,0);

   for(int i=0;i<HistoryDealsTotal();i++)
   {
      ulong tk=HistoryDealGetTicket(i);
      if(tk==0) continue;
      if((long)HistoryDealGetInteger(tk,DEAL_ENTRY)!=(long)DEAL_ENTRY_OUT) continue;

      double p=HistoryDealGetDouble(tk,DEAL_PROFIT);
      datetime tm=(datetime)HistoryDealGetInteger(tk,DEAL_TIME);
      double px=HistoryDealGetDouble(tk,DEAL_PRICE);
      bool win=(p>=0);
      if(win) wins++; else losses++;
      NR_DrawTradeMark(tk,tm,px,win);

      MqlDateTime dt; TimeToStruct(tm,dt);
      if(!win) dangerousHourCount[dt.hour]++;
   }

   string avoid="";
   for(int h=0; h<24; h++) if(dangerousHourCount[h]>=2) avoid += (avoid==""?"":",") + IntegerToString(h);

   state.AvoidHours=avoid;
   state.AvoidPatterns=(losses>wins?"fakeout,wick_spike,liquidity_grab":"");
   state.RiskModeNextDay=(losses>wins?"Cautious":"Normal");

   int f=FileOpen("modules\\night_review_flags.csv",FILE_WRITE|FILE_CSV|FILE_COMMON|FILE_ANSI);
   if(f!=INVALID_HANDLE)
   {
      FileWrite(f,"timestamp","wins","losses","avoid_hours","avoid_patterns","risk_mode_next_day");
      FileWrite(f,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),wins,losses,state.AvoidHours,state.AvoidPatterns,state.RiskModeNextDay);
      FileClose(f);
   }
}
