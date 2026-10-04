# Pivot points from the previous period. UNTESTED in thinkorswim: paste, check for errors, try in paperMoney.
# Charts > Studies > Edit Studies > Create. Levels only; this script cannot place orders.
input agg = {default DAY, WEEK};
def h = if agg == agg.DAY then high(period = AggregationPeriod.DAY)[1] else high(period = AggregationPeriod.WEEK)[1];
def l = if agg == agg.DAY then low(period = AggregationPeriod.DAY)[1] else low(period = AggregationPeriod.WEEK)[1];
def c = if agg == agg.DAY then close(period = AggregationPeriod.DAY)[1] else close(period = AggregationPeriod.WEEK)[1];
def pp = (h + l + c) / 3;
plot PP = pp;
plot S1 = 2 * pp - h;
plot S2 = pp - (h - l);
plot S3 = l - 2 * (h - pp);
plot R1 = 2 * pp - l;
plot R2 = pp + (h - l);
plot R3 = h + 2 * (pp - l);
PP.SetDefaultColor(Color.YELLOW);
S1.SetDefaultColor(Color.GREEN); S2.SetDefaultColor(Color.DARK_GREEN); S3.SetDefaultColor(Color.DARK_GREEN);
R1.SetDefaultColor(Color.RED); R2.SetDefaultColor(Color.DARK_RED); R3.SetDefaultColor(Color.DARK_RED);
