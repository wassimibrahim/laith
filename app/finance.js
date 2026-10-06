// All model inputs are hypothetical. EUR millions except TEU and EUR/TEU.
export const defaults = {teu:1000000,tariff:120,margin:45,growth:3,capacity:1800000,years:20,capex:8,da:6,nwc:8,tax:25,wacc:9,multiple:11,leverage:55,interest:6,tenor:15,hold:5,fees:2};
export function npv(rate, cashflows) { return cashflows.reduce((v,c,t)=>v+c/(1+rate)**t,0); }
export function irr(cashflows) {
  if(!cashflows.some(x=>x<0)||!cashflows.some(x=>x>0)) return null;
  const grid=[-.99,-.9,-.75,-.5,-.25,0,.05,.1,.2,.4,.8,1.5,3,10,100];
  const brackets=[];
  for(let i=1;i<grid.length;i++) {
    const a=npv(grid[i-1],cashflows),b=npv(grid[i],cashflows);
    if(a===0) return grid[i-1];
    if(a*b<=0) brackets.push([grid[i-1],grid[i]]);
  }
  if(brackets.length!==1) return null;
  let [lo,hi]=brackets[0];
  for(let i=0;i<150;i++){const mid=(lo+hi)/2;if(npv(lo,cashflows)*npv(mid,cashflows)<=0)hi=mid;else lo=mid;}
  return (lo+hi)/2;
}
export function model(input={}) {
  const p={...defaults,...input};
  for(const [k,v] of Object.entries(p)) if(!Number.isFinite(v)) throw new Error(`Invalid ${k}`);
  if(!['years','tenor','hold'].every(k=>Number.isInteger(p[k]))) throw new Error('Year inputs must be whole numbers.');
  if(p.years<1||p.tenor<1||p.hold<1||p.hold>=p.years||p.tenor>p.years||p.teu<=0||p.capacity<p.teu||p.wacc<=0||p.leverage<0||p.leverage>90) throw new Error('Check concession, holding period, capacity and financing inputs.');
  const revenue0=p.teu*p.tariff/1e6,ebitda0=revenue0*p.margin/100;
  const ev=ebitda0*p.multiple,fees=ev*p.fees/100,debt=ev*p.leverage/100,equity=ev+fees-debt;
  let balance=debt,prevRevenue=revenue0;
  const years=[];
  for(let y=1;y<=p.years;y++) {
    const volume=Math.min(p.capacity,p.teu*(1+p.growth/100)**y);
    const revenue=volume*p.tariff/1e6,ebitda=revenue*p.margin/100,da=revenue*p.da/100,ebit=ebitda-da;
    const capex=revenue*p.capex/100,deltaNwc=(revenue-prevRevenue)*p.nwc/100;
    const unleveredTax=Math.max(ebit,0)*p.tax/100,fcff=ebitda-unleveredTax-capex-deltaNwc;
    const interest=balance*p.interest/100,principal=y<=p.tenor?Math.min(balance,debt/p.tenor):0;
    const leveredTax=Math.max(ebit-interest,0)*p.tax/100,cfads=ebitda-leveredTax-capex-deltaNwc;
    const debtService=interest+principal,dscr=debtService>0?cfads/debtService:null;
    balance=y>=p.tenor?0:Math.max(0,balance-principal);
    if(balance<1e-9) balance=0;
    years.push({year:y,volume,revenue,ebitda,da,ebit,capex,deltaNwc,unleveredTax,fcff,interest,principal,leveredTax,cfads,dscr,debtService,balance,equityCF:cfads-debtService});
    prevRevenue=revenue;
  }
  const dcf=years.reduce((sum,y)=>sum+y.fcff/(1+p.wacc/100)**y.year,0);
  const exitEV=years.filter(y=>y.year>p.hold).reduce((s,y)=>s+y.fcff/(1+p.wacc/100)**(y.year-p.hold),0);
  const exitDebt=years[p.hold-1].balance,exitEquity=exitEV-exitDebt;
  const flows=[-equity,...years.slice(0,p.hold).map(y=>y.equityCF)]; flows[p.hold]+=exitEquity;
  const invested=-flows.filter(x=>x<0).reduce((a,b)=>a+b,0),received=flows.filter(x=>x>0).reduce((a,b)=>a+b,0);
  return {p,revenue0,ebitda0,ev,fees,debt,equity,years,dcf,exitEV,exitDebt,exitEquity,flows,irr:irr(flows),moic:invested>0?received/invested:null,minDSCR:Math.min(...years.filter(y=>y.dscr!==null).map(y=>y.dscr)),gap:dcf-ev};
}
export function debtCapacity(cfads, target, interest, tenor) {
  const service=cfads/target;
  return interest===0?service*tenor:service*(1-(1+interest)**(-tenor))/interest;
}
