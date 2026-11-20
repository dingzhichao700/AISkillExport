import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
import review_delivery as tool


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def manifest(self):
        Image.new('RGBA',(8,8),(255,0,0,255)).save(self.root/'evidence.png')
        self.put('sequence/animation.json',dict(scale=100,duration=100,pivot=dict(x=.5,y=.2)))
        Image.new('RGBA',(8,8)).save(self.root/'sequence/001.png')
        self.put('atlas.json',{})
        cfg = dict(scaleReview=dict(status='approved',evidence='evidence.png',approval='user record',geometryVersion='r1'),
            requiredAnimations=['Idle_R'],animations=[dict(key='Idle_R',sequence='sequence',
                atlases=[dict(png='evidence.png',json='atlas.json')],playbackClips=['Idle_R'])],
            previews=dict(sceneTransitions='evidence.png'),includesDeath=False,
            checks={key:dict(status='passed',evidence='atlas.json') for key in ('sequences','atlasRestore','timingPivot')})
        return cfg

    def test_inventory_and_blocked_cases(self):
        cfg = self.manifest()
        manifest = self.put('manifest.json',cfg)
        self.assertTrue(tool.check(manifest)['passed'])
        cfg['scaleReview']['status']='pending'
        self.assertFalse(tool.check(self.put('manifest.json',cfg))['passed'])
        cfg['scaleReview']['status']='approved'
        cfg['animations'][0]['playbackClips']=['part1','part2']
        self.assertFalse(tool.check(self.put('manifest.json',cfg))['passed'])
        cfg['animations'][0]['playbackClips']=['Idle_R']
        cfg['includesDeath']=True
        self.assertFalse(tool.check(self.put('manifest.json',cfg))['passed'])
        cfg['previews']['interruptedDeath']='evidence.png'
        cfg['requiredAnimations'].append('Move_R')
        self.assertFalse(tool.check(self.put('manifest.json',cfg))['passed'])

    def test_scene_scale_and_clipping(self):
        Image.new('RGBA',(100,100),(0,0,0,255)).save(self.root/'battle.png')
        Image.new('RGBA',(10,20),(255,0,0,255)).save(self.root/'unit.png')
        cfg=dict(background='battle.png',units=[dict(name='unit',frame='unit.png',displayScale=2,pivot=[.5,0],anchor=[50,80])])
        path=self.put('scene.json',cfg)
        tool.scene(path,self.root/'review.png')
        record=json.loads((self.root/'review.png.json').read_text())
        self.assertEqual(record['units'][0]['displayedCanvas'],[20,40])
        with Image.open(self.root/'review.png') as preview:
            self.assertEqual(preview.size,(100,100))
            self.assertEqual(preview.getpixel((40,40)),(255,0,0,255))
        cfg['units'][0]['anchor']=[0,0]
        with self.assertRaises(ValueError): tool.scene(self.put('scene.json',cfg),self.root/'bad.png')

    def test_archive_integrity_and_overwrite(self):
        self.put('package/sub/file.json',dict(data='hello'))
        tool.archive(self.root/'package',self.root/'package.zip')
        report=json.loads((self.root/'package.zip.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(len(report['entries']),1)
        with self.assertRaises(ValueError): tool.archive(self.root/'package',self.root/'package.zip')
        with self.assertRaises(ValueError): tool.archive(self.root/'package',self.root/'package/inside.zip')


if __name__=='__main__':
    unittest.main()
