#property strict

void VP_DrawTrendLine(const string name, datetime t1,double p1, datetime t2,double p2, color clr)
{
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_TREND,0,t1,p1,t2,p2);
   ObjectMove(0,name,0,t1,p1); ObjectMove(0,name,1,t2,p2);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
}

void VP_DrawSR(const string sym)
{
   double h=iHigh(sym,PERIOD_H1,iHighest(sym,PERIOD_H1,MODE_HIGH,60,1));
   double l=iLow(sym,PERIOD_H1,iLowest(sym,PERIOD_H1,MODE_LOW,60,1));
   if(ObjectFind(0,"VP_SR_H")<0) ObjectCreate(0,"VP_SR_H",OBJ_HLINE,0,0,h);
   if(ObjectFind(0,"VP_SR_L")<0) ObjectCreate(0,"VP_SR_L",OBJ_HLINE,0,0,l);
   ObjectSetDouble(0,"VP_SR_H",OBJPROP_PRICE,h); ObjectSetInteger(0,"VP_SR_H",OBJPROP_COLOR,clrOrangeRed);
   ObjectSetDouble(0,"VP_SR_L",OBJPROP_PRICE,l); ObjectSetInteger(0,"VP_SR_L",OBJPROP_COLOR,clrDeepSkyBlue);
}

void VP_DrawZone(const string name, datetime t1,double top, datetime t2,double bottom, color clr)
{
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_RECTANGLE,0,t1,top,t2,bottom);
   ObjectMove(0,name,0,t1,top); ObjectMove(0,name,1,t2,bottom);
   ObjectSetInteger(0,name,OBJPROP_BACK,true); ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
}

void VP_DrawStructureLabel(const string name, datetime t, double p, const string text, color clr)
{
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_TEXT,0,t,p);
   ObjectMove(0,name,0,t,p); ObjectSetString(0,name,OBJPROP_TEXT,text); ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
}

void VP_DrawSignalArrow(const string name, datetime t, double p, bool buy)
{
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_ARROW,0,t,p);
   ObjectMove(0,name,0,t,p); ObjectSetInteger(0,name,OBJPROP_ARROWCODE,buy?233:234); ObjectSetInteger(0,name,OBJPROP_COLOR,buy?clrLime:clrTomato);
}

void VP_DrawSLTP(const string slName,const string tpName,double sl,double tp)
{
   if(ObjectFind(0,slName)<0) ObjectCreate(0,slName,OBJ_HLINE,0,0,sl);
   if(ObjectFind(0,tpName)<0) ObjectCreate(0,tpName,OBJ_HLINE,0,0,tp);
   ObjectSetDouble(0,slName,OBJPROP_PRICE,sl); ObjectSetInteger(0,slName,OBJPROP_COLOR,clrTomato);
   ObjectSetDouble(0,tpName,OBJPROP_PRICE,tp); ObjectSetInteger(0,tpName,OBJPROP_COLOR,clrLime);
}

void VP_UpdatePanel(const string h4Trend,const string h1Structure,const string volatilityMode,const string atrMode,const string newsMode,const string riskMode)
{
   string name="VP_INFO_PANEL";
   string txt="H4 Trend: "+h4Trend+"\nH1 Structure: "+h1Structure+"\nVolatility Mode: "+volatilityMode+
              "\nATR Mode: "+atrMode+"\nNews Mode: "+newsMode+"\nRisk Mode: "+riskMode;
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_LABEL,0,0,0);
   ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_RIGHT_UPPER);
   ObjectSetInteger(0,name,OBJPROP_XDISTANCE,10);
   ObjectSetInteger(0,name,OBJPROP_YDISTANCE,20);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clrWhite);
   ObjectSetString(0,name,OBJPROP_TEXT,txt);
}
