/** Validate an Artifact Session export before publishing the editable A3 source. */
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const options=Object.fromEntries(process.argv.slice(2).reduce((pairs,value,i,all)=>{if(i%2===0)pairs.push([value.replace(/^--/,''),all[i+1]]);return pairs;},[]));
for(const key of ['runtime-modules','skill-dir','python-executable'])if(!options[key])throw Error('Missing --'+key);
process.env.RUNTIME_NODE_MODULES=options['runtime-modules'];
const skill=options['skill-dir'];
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:root,
  candidatePath:path.join(root,options.candidate??'.codex-build/scenarios-2026-10-30/candidate.pptx'),
  finalPath:path.join(root,options.output??'outputs/current/Scenarios_A3_2026-10-30.pptx'),
  explicitTotalSlideCount:3,
  pythonExecutable:options['python-executable'],
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','15120000,10692000','--validate-heading-fit'],
  requiredNativeTableOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},
  verifyArtifactToolImport:true,
  receiptPath:path.join(root,options.receipt??'.codex-build/scenarios-2026-10-30/validation.json')});
console.log(JSON.stringify(result));
