type Workspace = "studio" | "cloud";
const explorer = "https://rajkumar0rk.github.io/BTC-Analysis/";
const cloud = "https://btc-analysis.rajkumar55853.workers.dev";
export function WorkspaceNav({current}:{current:Workspace}) {
 const links = [
  {id:"explorer",label:"Backtest Explorer",href:current==="studio"?"../":explorer},
  {id:"studio",label:"Strategy Studio",href:current==="studio"?"./":explorer+"studio/"},
  {id:"cloud",label:"Private Cloud",href:current==="cloud"?"./":cloud},
 ] as const;
 return <nav className="workspace-nav" aria-label="Workspace navigation">{links.map(link=><a key={link.id} href={link.href} rel="noreferrer" aria-current={link.id===current?"page":undefined}>{link.label}</a>)}</nav>;
}
