"""Reproduce Stage 1B identity/design audit from the verified Stage 1A artifact.

Only existing pilot numeric completeness is examined. No phenotype statistics,
reference AP calculation, normalization, evaluation tuning or image pixels.
"""
from __future__ import annotations
import argparse, csv, gzip, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path
from cohort_tools import *

PILOT='jump-cellpainting__2024_Chandrasekaran_NatureMethods_CPJUMP1'
PROTOCOL='carpenter-singh-lab__2023_Cimini_NatureProtocols'
PUBLIC='jump-cellpainting__pilot-data-public'
SCOPE='jump-cellpainting__jump-scope'
BATCH='2020_11_04_CPJUMP1'
STAIN5=tuple('BR001205'+str(i) for i in range(23,27))
STAIN4=tuple('BR001166'+str(i) for i in range(29,32))
REAGENT=tuple(f'CPJUMP{i:03d}' for i in range(1,5))
SCOPEPLATES=tuple('CP_Broad_Phenix_C_BIN1_1Plane_P'+str(i) for i in range(1,5))

def indexed(rows,key):
    d={}
    for r in rows:
        k=r[key]
        if k in d: raise ValueError('Nonunique key: '+k)
        d[k]=r
    return d


def run(root,out):
    start=time.monotonic();root=Path(root);out=Path(out);s=root/'source-data/repos'
    refs=[]
    def table(slug,rel,encoding='utf-8-sig'):
        p=s/slug/rel
        refs.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha256(p),
                     'encoding':encoding,'role':'design_or_identity_metadata'})
        return read_table(p,encoding=encoding)[1]
    annot=table(PILOT,'metadata/external_metadata/JUMP-Target-1_compound_metadata.tsv')
    layout=table(PILOT,f'metadata/platemaps/{BATCH}/platemap/JUMP-Target-1_compound_platemap.txt')
    barcodes=table(PILOT,f'metadata/platemaps/{BATCH}/barcode_platemap.csv')
    bm=indexed(barcodes,'Assay_Plate_Barcode')
    exppath=s/PILOT/'benchmark/output/experiment-metadata.tsv'
    exp=table(PILOT,'benchmark/output/experiment-metadata.tsv')
    design=[];wellrows=[];profiles=[];headers=[]
    for plate in PLATES:
        er=[r for r in exp if r['Batch']==BATCH and r['Assay_Plate_Barcode']==plate]
        if len(er)!=1: raise ValueError('Pilot experimental design join not one to one')
        er=er[0]
        expected={'Perturbation':'compound','Cell_type':'A549','Time':'48','Density':'100',
                  'Antibiotics':'absent','Cell_line':'Parental','Time_delay':'Day0','Times_imaged':'1','Anomaly':'none'}
        if any(er[k]!=v for k,v in expected.items()): raise ValueError('Pilot condition differs')
        if bm[plate]['Plate_Map_Name']!='JUMP-Target-1_compound_platemap':raise ValueError('Pilot barcode layout differs')
        summary,header,ws=inspect_profile(root/f'data/pilot/{plate}.csv',plate,numeric_qc=True)
        if summary['missing_wells']:raise ValueError('Pilot wells missing')
        headers.append(header)
        profiles.append({'plate':plate,'path':f'data/pilot/{plate}.csv','sha256':sha256(root/f'data/pilot/{plate}.csv'),**summary})
        ds={'dataset':'cpg0000-jump-pilot','physical_plate_id':plate,'acquisition_id':BATCH+'/'+plate,
            'preparation_group':BATCH,'cell_line':'A549','genetic_state':'Parental','dose_um':5,
            'dose_evidence':'Chandrasekaran et al 2024 Methods / Experimental conditions / Compounds',
            'exposure_hours':48,'seed_cells_per_well':1000,'imaging_repeat':1,
            'condition_id':'PILOT_A549_PARENTAL_48H_5UM_1000CELLS_DAY0',
            'replication_level':'four physical plates within one experiment, not four independent batches'}
        design.append(ds)
        joined=join_wells(ws,layout,annot)
        for w in joined:
            w.update({k:ds[k] for k in ['dataset','physical_plate_id','acquisition_id','preparation_group','cell_line','condition_id','exposure_hours','seed_cells_per_well']})
            # DMSO is not assigned a fictitious 5 uM small-molecule treatment.
            w['dose_um']=5 if w['role']!='negative_control' else ''
            w['dose_status']='PUBLISHED_APPLIED_DOSE' if w['role']!='negative_control' else 'NOT_APPLICABLE_NEGATIVE_CONTROL'
            w['negative_control_evidence']='frozen blank annotation explicitly control/negcon' if w['role']=='negative_control' else ''
        wellrows+=joined
    if any(h!=headers[0] for h in headers):raise ValueError('Pilot feature headers differ')
    write_table(out/'manifests/pilot-well-design.tsv',wellrows)
    write_table(out/'manifests/pilot-plate-design.tsv',design)
    dump(out/'evidence/pilot-profile-integrity.json',profiles)
    rawsamples=[r for r in annot if r['broad_sample']]
    namegroups=defaultdict(list)
    for r in rawsamples:namegroups[r['pert_iname']].append(r)
    collisions=[{'compound_name':name,'sample_ids':';'.join(r['broad_sample'] for r in rows),
                 'source_inchikeys':';'.join(r['InChIKey'] for r in rows),
                 'action':'KEEP_DISTINCT_SOURCE_SAMPLES; no name-only collapse'} for name,rows in namegroups.items() if len(rows)>1]
    write_table(out/'manifests/pilot-name-collisions.tsv',collisions,['compound_name','sample_ids','source_inchikeys','action'])
    pairs=design_pair_counts(wellrows)
    spatial=design_pair_counts(wellrows,True)
    write_table(out/'manifests/pilot-pair-counts.tsv',pairs)
    write_table(out/'manifests/pilot-different-position-pair-counts.tsv',spatial)
    bysample=defaultdict(list)
    for w in wellrows:
        if w['role']!='negative_control':bysample[w['sample_id']].append(w)
    replicate_rows=[]
    for sample,ws in sorted(bysample.items()):
        replicate_rows.append({'sample_id':sample,'compound_name':ws[0]['compound_name'],
          'n_wells':len(ws),'physical_plates':len({w['physical_plate_id'] for w in ws}),
          'preparation_groups':len({w['preparation_group'] for w in ws}),
          'distinct_positions':len({w['well'] for w in ws}),
          'positions':';'.join(sorted({w['well'] for w in ws})),
          'position_limitation':'complete sample-position confounding' if len({w['well'] for w in ws})==1 else 'two within-plate positions; restricted cross-position assessment feasible'})
    write_table(out/'manifests/pilot-replicate-groups.tsv',replicate_rows)
    # Schema-only feature dictionary. Tags are not a fitted/final feature selection.
    feature_rows=[];familycounts=Counter();brightfield=0
    allchannels=CHANNELS+('Brightfield','HighZBF','LowZBF')
    for feature in headers[0][2:]:
        tok=feature.split('_');channels=[c for c in allchannels if c in tok];family=tok[1];familycounts[family]+=1
        hasbf=any(c in channels for c in ['Brightfield','HighZBF','LowZBF']);brightfield+=hasbf
        feature_rows.append({'feature':feature,'compartment':tok[0],'family':family,
          'explicit_channel_tokens':';'.join(channels),'has_brightfield_dependency':hasbf,
          'technical_or_position_review':family in ['Location','Parent','Children','Number'] or any(x in tok for x in ['BoundingBoxMaximum','BoundingBoxMinimum','Center']),
          'segmentation_dependency':'nucleus from CorrBlue; cells from RNA; cytoplasm = cells minus nuclei; see pipeline',
          'status':'SCHEMA_TAG_ONLY_NOT_FINAL_FEATURE_MASK'})
    write_table(out/'manifests/pilot-feature-dictionary.tsv',feature_rows)
    # Curate genuine fluorescent field references; exclude illumination functions and BF.
    imgpath=root/'manifests/image-references.tsv';unique={};key_to_file={};total=0;selected=0;allfield=set()
    with imgpath.open(encoding='utf-8',newline='') as f:
      for r in csv.DictReader(f,delimiter='\t'):
        total+=1
        if r['channel_source_label'] not in ['Orig'+c for c in CHANNELS]:continue
        selected+=1;k=tuple(r[x] for x in ['plate','well','site','channel_source_label'])
        v=(r['source_directory'],r['source_filename'])
        if k in key_to_file and key_to_file[k]!=v:raise ValueError('Conflicting image-to-field references')
        key_to_file[k]=v
        if k not in unique:
            x={**r,'source_records_collapsed':1,'kind':'original_fluorescence_reference','image_bytes_verified':False,
               'note':'source_directory is upstream path, NOT a verified current download URL'};unique[k]=x
        else:unique[k]['source_records_collapsed']+=1
        allfield.add((r['plate'],r['well'],int(r['site'])))
    imageout=out/'manifests/pilot-fluorescence-image-references.tsv.gz';imageout.parent.mkdir(parents=True,exist_ok=True)
    with imageout.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
        import io
        with io.TextIOWrapper(gz,encoding='utf-8',newline='') as text:
            writer=csv.DictWriter(text,fieldnames=list(next(iter(unique.values()))),delimiter='\t',lineterminator='\n')
            writer.writeheader();writer.writerows(unique[k] for k in sorted(unique))
    missing=sorted((p,f'{chr(65+r)}{c:02d}',site) for p in PLATES for r in range(16) for c in range(1,25) for site in range(1,17) if (p,f'{chr(65+r)}{c:02d}',site) not in allfield)
    write_table(out/'manifests/pilot-missing-image-sites.tsv',[dict(zip(['plate','well','site'],x)) for x in missing],['plate','well','site'])
    imgsummary={'source_reference_rows':total,'fluorescence_reference_rows_before_deduplication':selected,
                'unique_original_fluorescence_references':len(unique),'unique_field_positions':len(allfield),
                'missing_field_positions':missing,'pixels_downloaded':0,
                'note':'16 nominal sites per well from source mapping; two absent site records. All wells still have profile rows.'}
    dump(out/'evidence/image-mapping-audit.json',imgsummary)
    # Protocol uses a documented single-byte micro sign; no lossy fallback.
    master=table(PROTOCOL,'JUMPExperimentMasterTable.csv','cp1252')
    cohorts=[];protocolrows=[];layoutsummary=[];layout_samples={}
    choices=[('protocol_stain5_thermo_standard', 'Stain5',STAIN5,'Stain5_CondAB_Standard','Widefield'),
             ('protocol_reagent1_thermo_standard','Reagent1',REAGENT,'2020_12_11_Reagent1_Pfizer','Widefield'),
             ('protocol_stain4_standard','Stain4',STAIN4,'2020_09_22_Stain4_Standard','Widefield')]
    for cid,batch,plates,folder,modality in choices:
        bc=table(PUBLIC,f'metadata/platemaps/{folder}/barcode_platemap.csv');bybc=indexed(bc,'Assay_Plate_Barcode')
        lay=table(PUBLIC,f'metadata/platemaps/{folder}/platemap/JUMP-MOA_compound_platemap_with_metadata.txt')
        ls=join_wells([{'plate':'DESIGN_TEMPLATE','well':r['well_position']} for r in lay],lay)
        sm=[r for r in ls if r['role']!='negative_control'];layout_samples[cid]={r['sample_id']:r for r in sm}
        layoutsummary.append({'cohort':cid,'template_wells':len(ls),'negative_control_wells_per_plate':sum(r['role']=='negative_control' for r in ls),'sample_ids':len(layout_samples[cid]),'source_named_sample_ids':sum(bool(r['source_inchikey']) for r in layout_samples[cid].values()),'anonymous_or_missing_chemical_ids':[k for k,r in layout_samples[cid].items() if not r['source_inchikey']],'replicates_per_sample_per_plate':dict(Counter(Counter(r['sample_id'] for r in sm).values())),
                              'source_library_column':'mmoles_per_liter=1.5 for treated wells; NOT assumed final assay concentration'})
        for plate in plates:
            mr=[(i,r) for i,r in enumerate(master,2) if r['Batch']==batch and r['Plate barcode']==plate and r['Imaging modality']==modality and not r['Other experimental tests']]
            if len(mr)!=1:raise ValueError(f'{cid}:{plate} has {len(mr)} eligible master records')
            i,m=mr[0]
            if m['Cell type']!='U2OS' or m['Treatment timepoint']!='48' or m['Reagent source']!='Thermo Fisher':raise ValueError('Protocol condition not matched')
            if bybc[plate]['Plate_Map_Name']!='JUMP-MOA_compound_platemap_with_metadata':raise ValueError('Protocol mapping differs')
            d={k:v for k,v in m.items() if k!='Qualitative conclusion drawn (if any)'}
            d.update({'cohort_id':cid,'master_record':i,'layout_folder':folder,'physical_plate_id':plate,'dose_um':'',
                      'dose_status':'UNRESOLVED_APPLIED_COMPOUND_DOSE; source library concentration is not verified assay concentration'})
            protocolrows.append(d)
        cohorts.append({'cohort_id':cid,'plates':list(plates),'n_physical_plates_design':len(plates),'cell_line':'U2OS','exposure_hours':48,
                        'seed_cells_per_well':int(protocolrows[-1]['Plating density (if known)']),'reagent_supplier':'Thermo Fisher','dose_um':None,
                        'status':'CANDIDATE_PENDING_RAW_PROFILES_AND_APPLIED_DOSE','template_controls_per_plate':24,
                        'potential_role':{'Stain5':'development','Reagent1':'independent_batch_candidate_with_site_and_processing_checks','Stain4':'2000_cell_context_candidate'}[batch]})
    write_table(out/'manifests/protocol-selected-design.tsv',protocolrows)
    # All repeated acquisitions retained as aliases, never count them as new plates.
    aliases=[{'batch':r['Batch'],'physical_plate_id':r['Plate barcode'],'condition_label':r['Condition shorthand'],
              'modality':r['Imaging modality'],'other_tests':r['Other experimental tests'],'profile_folder':r['Profile folder on GH'],
              'master_record':i,'classification':'shared barcode: same physical plate group'} for i,r in enumerate(master,2)
              if r['Plate barcode'] in STAIN5+STAIN4+REAGENT]
    write_table(out/'manifests/protocol-acquisition-aliases.tsv',aliases)
    scopelay=table(SCOPE,'metadata/platemaps/Scope1_PE_Bin1_Confocal_1Plane/platemap/JUMP-MOA_compound_platemap.txt')
    scopeann=table(SCOPE,'metadata/external_metadata/JUMP-MOA_compound_metadata.tsv')
    scopebc=table(SCOPE,'metadata/platemaps/Scope1_PE_Bin1_Confocal_1Plane/barcode_platemap.csv')
    for p in SCOPEPLATES:
        if indexed(scopebc,'Assay_Plate_Barcode')[p]['Plate_Map_Name']!='JUMP-MOA_compound_platemap':raise ValueError('Scope layout differs')
    sl=join_wells([{'plate':'DESIGN_TEMPLATE','well':r['well_position']} for r in scopelay],scopelay,scopeann)
    scsamples={r['sample_id']:r for r in sl if r['role']!='negative_control'};layout_samples['scope_pe_c_bin1_1plane']=scsamples
    layoutsummary.append({'cohort':'scope_pe_c_bin1_1plane','template_wells':len(sl),'negative_control_wells_per_plate':sum(r['role']=='negative_control' for r in sl),'sample_ids':len(scsamples),'replicates_per_sample_per_plate':dict(Counter(Counter(r['sample_id'] for r in sl if r['role']!='negative_control').values()))})
    dump(out/'evidence/moa-layout-audit.json',layoutsummary)
    cohorts.append({'cohort_id':'scope_pe_c_bin1_1plane','plates':list(SCOPEPLATES),'n_physical_plate_labels':4,
                    'physical_identity_status':'P1-P4 acquisition labels; conservatively group all PE variants by suffix. Need authors mapping to exact preparations.',
                    'cell_line':'U2OS','dose_um':3,'dose_evidence':'Tromans-Coia 2023 Methods 4.1','seed_cells_per_well':2000,'exposure_hours':None,
                    'status':'CANDIDATE_PENDING_RAW_PROFILES_EXPOSURE_AND_PHYSICAL_MAPPING',
                    'potential_role':'acquisition/context transportability, not matched 1000-cell biological validation'})
    # Historical annotation comparisons and cross-cohort sample keys.
    cross=[]
    layout_samples['pilot_a549']={r['broad_sample']:{'source_inchikey':r['InChIKey'],'compound_name':r['pert_iname']} for r in rawsamples}
    keys=list(layout_samples)
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            aa,bb=layout_samples[a],layout_samples[b];common=set(aa)&set(bb)
            cross.append({'left':a,'right':b,'exact_sample_id_overlap':len(common),
                         'same_nonblank_source_inchikey_for_exact_id':sum(bool(aa[k]['source_inchikey']) and aa[k]['source_inchikey']==bb[k]['source_inchikey'] for k in common),
                         'public_brd_sample_id_overlap':sum(k.startswith('BRD-') for k in common),
                         'anonymous_label_overlap_not_proof_of_identity':sum(not k.startswith('BRD-') for k in common),
                         'metadata_overlap_only_not_validated_condition_match':True})
    write_table(out/'manifests/cross-cohort-identity-overlap.tsv',cross)
    current=table('jump-cellpainting__JUMP-Target','JUMP-Target-1_compound_metadata.tsv')
    current=indexed(current,'broad_sample')
    changes=[]
    for r in rawsamples:
        rr=current.get(r['broad_sample'])
        if rr is None:raise ValueError('Frozen sample missing from current Target annotation')
        ik=next(k for k in rr if k.lower()=='inchikey')
        if rr[ik]!=r['InChIKey']:
            changes.append({'sample_id':r['broad_sample'],'compound_name':r['pert_iname'],
                            'frozen_inchikey':r['InChIKey'],'current_inchikey':rr[ik],
                            'action':'retain frozen key; do not rewrite silently'})
    write_table(out/'manifests/annotation-version-conflicts.tsv',changes,['sample_id','compound_name','frozen_inchikey','current_inchikey','action'])
    objects=json.loads((root/'manifests/external-objects.json').read_text())
    pe=[]
    for o in objects:
        key=o['key'];pp=Path(key)
        if '/backend/2020_11_16_Scope1_PE/' in key and pp.name==pp.parent.name+'.csv.gz' and pp.parent.name.startswith('CP_Broad_Phenix_'):
            m=re.search(r'_P([1-4])$',pp.parent.name)
            if not m:raise ValueError('Unrecognized PE plate suffix')
            pe.append({'source_key':key,'acquisition_plate_label':pp.parent.name,'conservative_material_group':'SCOPE_PE_P'+m[1],
                       'classification':'same suffix grouped to prevent repeat-image leakage; source mapping still required'})
    write_table(out/'manifests/scope-conservative-acquisition-groups.tsv',pe)
    summary={'pilot':{'wells':len(wellrows),'per_plate':{p:dict(Counter(r['role'] for r in wellrows if r['plate']==p)) for p in PLATES},
                'source_sample_ids':len(rawsamples),'source_inchikeys':len({r['InChIKey'] for r in rawsamples}),
                'unique_display_names':len(namegroups),'duplicate_display_name_groups':len(collisions),
                'single_position_samples':sum(r['distinct_positions']==1 for r in replicate_rows),
                'multiple_position_samples':sum(r['distinct_positions']>1 for r in replicate_rows),
                'cross_plate_query_count':len(pairs),'cross_plate_directed_positive_pairs':sum(r['eligible_positives'] for r in pairs),
                'cross_plate_directed_negative_pairs':sum(r['eligible_negatives'] for r in pairs),
                'different_position_assessable_queries':sum(r['assessable_by_design'] for r in spatial),
                'current_annotation_key_changes':len(changes),'feature_families':dict(familycounts),
                'brightfield_dependent_columns':brightfield,'all_prefixed_columns':len(headers[0])-2,
                'status':'ACCEPTED_FOR_BOUNDED_REFERENCE_AND_WITHIN_EXPERIMENT_ANALYSIS_WITH_POSITION_LIMITATION'},
             'images':imgsummary,'external_candidates':cohorts,'scope_pe_acquisitions':len(pe),
             'scope_pe_conservative_material_groups':len({r['conservative_material_group'] for r in pe}),
             'stage1_gate':'BLOCKED_PENDING_TARGETED_PROFILES_AND_EXTERNAL_METADATA',
             'stage2_started':False,'elapsed_seconds':time.monotonic()-start}
    dump(out/'evidence/cohort-audit-summary.json',summary)
    dump(out/'manifests/audit-input-sources.json',refs)
    # JSON is valid YAML 1.2; avoids adding an untested dependency to this substage.
    dump(out/'configs/cohorts.yaml',{'schema':1,'stage1_passed':False,'pilot':summary['pilot'],
          'pilot_plates':design,'external_candidates':cohorts,
          'prohibited_comparison_roles':['A549 and U2OS as matched replicates','1000 and 2000 seeded cells as same condition',
          'reimages of same material as independent experiments','source library mM as applied compound dose',
          'display-name-only compound collapse'],
          'stage2_authorized':False})
    print(json.dumps(summary,indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.input,a.output)
