#property strict

#include "AutoModuleEngine.mqh"
#include "modules/AnalysisModule.mqh"
#include "modules/VisualPanel.mqh"
#include "modules/NightReview.mqh"

input double InpMaxSpreadPips = 30.0;
input double InpMinAtrPips = 8.0;
input double InpExplosionPipsPerSec = 80.0;

AnalysisState g_state;
ScalpingGuards g_guards;
NightReviewState g_night;

int OnInit()
{
   if(!EnsureAutoModules())
   {
      Print("AUTO-MODULE ENGINE failed to initialize modules.");
      return(INIT_FAILED);
   }
   Print("AUTO-MODULE ENGINE ready.");
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   // Existing strategy logic remains untouched (call original logic here).
   // Modules run in parallel as intelligence extensions.

   RunAnalysisModule(_Symbol,g_state,g_guards,InpMaxSpreadPips,InpMinAtrPips,InpExplosionPipsPerSec);

   string trend=(g_state.TrendDirection>0?"Bullish":(g_state.TrendDirection<0?"Bearish":"Neutral"));
   string risk=(g_state.RiskMode==RISK_NORMAL?"Normal":(g_state.RiskMode==RISK_CAUTIOUS?"Cautious":"Blocked"));
   VP_DrawSR(_Symbol);
   VP_UpdatePanel(trend,DoubleToString(g_state.StructureClarity,1),g_state.ChopDetected?"Chop":"Trend",g_state.ATRMode,"Auto",risk);

   RunNightReview(g_night);
}
