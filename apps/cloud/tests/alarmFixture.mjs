// TEST ONLY. Never use this entrypoint for a production release.
import worker from "../src/worker.mjs";
import {PaperLane as Base} from "../src/paperObject.mjs";
import {parseCandle} from "../src/paperEngine.mjs";
export class PaperLane extends Base{
 async candle(_symbol,t){return parseCandle({time:t/1000,open:100,high:100,low:100,close:100},t);}
}
export default worker;
