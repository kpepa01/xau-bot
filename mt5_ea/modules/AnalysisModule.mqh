#property strict

enum RiskModeEnum { RISK_NORMAL=0, RISK_CAUTIOUS=1, RISK_BLOCKED=2 };

struct AnalysisState {
   int TrendDirection;
   double TrendStrength;
   double StructureClarity;
   bool ChopDetected;
   string ATRMode;
   RiskModeEnum RiskMode;
   bool FakeBreakout;
   bool WickSpike;
   bool SpreadBlocked;
   bool CandleExplosionBlocked;
   bool NearDailyExtremes;
   bool LiquidityGrabWait;
   double ConfirmationScore;
};

struct ScalpingGuards {
   datetime ExplosionBlockUntil;
   double LastTickPrice;
   datetime LastTickTime;
};

bool AM_WickToBodyTooLarge(string sym, ENUM_TIMEFRAMES tf, int shift=0)
{
   double o=iOpen(sym,tf,shift), c=iClose(sym,tf,shift), h=iHigh(sym,tf,shift), l=iLow(sym,tf,shift);
   double body=MathAbs(c-o);
   if(body<=_Point) return true;
   double wick=MathMax(h-MathMax(o,c), MathMin(o,c)-l);
   return wick>body;
}

bool AM_FakeBreakout(string sym, ENUM_TIMEFRAMES tf, int shift=0)
{
   double h1=iHigh(sym,tf,shift+1), l1=iLow(sym,tf,shift+1);
   double h0=iHigh(sym,tf,shift), l0=iLow(sym,tf,shift), c0=iClose(sym,tf,shift);
   if(h0>h1 && c0<h1) return true;
   if(l0<l1 && c0>l1) return true;
   return false;
}

bool AM_IsNearDailyHighLow(string sym,double thresholdPips)
{
   double dayHigh=iHigh(sym,PERIOD_D1,0), dayLow=iLow(sym,PERIOD_D1,0);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   double p=SymbolInfoDouble(sym,SYMBOL_POINT);
   double dist=MathMin(MathAbs(dayHigh-bid),MathAbs(bid-dayLow))/MathMax(p,1e-8);
   return dist<=thresholdPips;
}

bool AM_NoTradeBeforeNewCandle(ENUM_TIMEFRAMES tf,int secondsBefore=300)
{
   datetime open=iTime(_Symbol,tf,0);
   int sec=(int)PeriodSeconds(tf);
   int remain=(int)(open+sec-TimeCurrent());
   return (remain<=secondsBefore);
}

bool AM_DetectCandleExplosion(string sym,ScalpingGuards &g,double movePipsPerSec)
{
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   datetime now=TimeCurrent();
   double pt=SymbolInfoDouble(sym,SYMBOL_POINT);
   if(g.LastTickTime==0){ g.LastTickTime=now; g.LastTickPrice=bid; return false; }
   double dt=(double)(now-g.LastTickTime);
   if(dt<=0) return false;
   double pips=MathAbs(bid-g.LastTickPrice)/MathMax(pt,1e-8);
   g.LastTickPrice=bid; g.LastTickTime=now;
   if((pips/dt)>=movePipsPerSec){ g.ExplosionBlockUntil=now+60; return true; }
   return (now<g.ExplosionBlockUntil);
}

void RunAnalysisModule(string sym, AnalysisState &st, ScalpingGuards &guards,
                       double maxSpreadPips=30.0, double minAtrPips=8.0,
                       double explosionPipsPerSec=80.0)
{
   double point=SymbolInfoDouble(sym,SYMBOL_POINT);
   double spread=(SymbolInfoDouble(sym,SYMBOL_ASK)-SymbolInfoDouble(sym,SYMBOL_BID))/MathMax(point,1e-8);
   st.SpreadBlocked=(spread>maxSpreadPips);

   double eH4f=iMA(sym,PERIOD_H4,20,0,MODE_EMA,PRICE_CLOSE,0), eH4s=iMA(sym,PERIOD_H4,50,0,MODE_EMA,PRICE_CLOSE,0);
   double eH1f=iMA(sym,PERIOD_H1,20,0,MODE_EMA,PRICE_CLOSE,0), eH1s=iMA(sym,PERIOD_H1,50,0,MODE_EMA,PRICE_CLOSE,0);
   double eM15f=iMA(sym,PERIOD_M15,20,0,MODE_EMA,PRICE_CLOSE,0), eM15s=iMA(sym,PERIOD_M15,50,0,MODE_EMA,PRICE_CLOSE,0);

   int h4=(eH4f>eH4s)?1:((eH4f<eH4s)?-1:0);
   int h1=(eH1f>eH1s)?1:((eH1f<eH1s)?-1:0);
   int m15=(eM15f>eM15s)?1:((eM15f<eM15s)?-1:0);
   st.TrendDirection=(h4==h1 && h1==m15)?h4:0;

   double atr=iATR(sym,PERIOD_H1,14,0)/MathMax(point,1e-8);
   st.ATRMode=(atr<minAtrPips?"LOW":"NORMAL");

   st.ChopDetected=(MathAbs(eH1f-eH1s)<=iATR(sym,PERIOD_H1,14,0)*0.12);
   st.FakeBreakout=AM_FakeBreakout(sym,PERIOD_M15,0);
   st.WickSpike=AM_WickToBodyTooLarge(sym,PERIOD_M15,0);
   st.CandleExplosionBlocked=AM_DetectCandleExplosion(sym,guards,explosionPipsPerSec);
   st.NearDailyExtremes=AM_IsNearDailyHighLow(sym,45.0);
   st.LiquidityGrabWait=st.FakeBreakout;

   st.TrendStrength=MathMin(100.0,MathAbs(eH1f-eH1s)/MathMax(point,1e-8));
   st.StructureClarity=MathMin(100.0,MathAbs(iClose(sym,PERIOD_H1,0)-iOpen(sym,PERIOD_H1,0))/MathMax(iATR(sym,PERIOD_H1,14,0),point)*100.0);

   st.ConfirmationScore=0;
   st.ConfirmationScore += (h4!=0 && h4==h1 ? 35.0 : 0.0);
   st.ConfirmationScore += (h1!=0 && h1==m15 ? 35.0 : 0.0);
   st.ConfirmationScore += (!st.ChopDetected ? 15.0 : 0.0);
   st.ConfirmationScore += (!st.WickSpike ? 15.0 : 0.0);

   st.RiskMode=RISK_NORMAL;
   if(st.ChopDetected || st.WickSpike || st.ATRMode=="LOW") st.RiskMode=RISK_CAUTIOUS;
   if(st.SpreadBlocked || st.CandleExplosionBlocked || st.NearDailyExtremes || st.LiquidityGrabWait || st.TrendDirection==0) st.RiskMode=RISK_BLOCKED;
}
