const base = import.meta.env.VITE_API_BASE || '';
export async function api<T>(path:string, options:RequestInit = {}):Promise<T> {
  const response = await fetch(base+'/api'+path,{...options,headers:{...(options.body instanceof FormData ? {} : {'Content-Type':'application/json'}),...options.headers}});
  if (!response.ok) {const error = await response.json().catch(()=>({detail:'Server request failed'})); throw new Error(typeof error.detail==='string'?error.detail:`Request failed (${response.status})`);}
  return response.json();
}
export const json = (method:string, body?:unknown):RequestInit => ({method,body:body===undefined?undefined:JSON.stringify(body)});
export function time(value:string) {return new Date(value).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});}
export function label(value:string|null|undefined) {const names:Record<string,string>={ang:'Anger',hap:'Happiness',neu:'Neutral',sad:'Sadness',mixed_signals:'Mixed signals',unknown:'Unknown'};return value ? names[value]||value.replace(/_/g,' ') : 'Unavailable';}
