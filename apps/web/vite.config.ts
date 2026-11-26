import {defineConfig} from "vite";
const proxy={"/v1":"http://127.0.0.1:8000","/health":"http://127.0.0.1:8000"};
export default defineConfig(({mode})=>({base:mode==="pages"?"./":"/",plugins:mode==="private"?[{name:"private-release-marker",generateBundle(){this.emitFile({type:"asset",fileName:"private-release.json",source:'{"mode":"private"}'});}}]:[],server:{host:"127.0.0.1",port:5173,strictPort:true,proxy},preview:{host:"127.0.0.1",port:4173,strictPort:true,proxy}}));
