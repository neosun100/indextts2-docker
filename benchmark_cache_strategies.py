"""
四种缓存策略性能对比测试
1. 无缓存 (No Cache)
2. 磁盘缓存 (Disk Cache)
3. 内存缓存 (RAM Cache)
4. 显存缓存 (VRAM Cache - 同一说话人连续调用)
"""
import time
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any


class CacheBenchmark:
    def __init__(self):
        self.test_speakers = [
            "/app/examples/voice_01.wav",
            "/app/examples/voice_02.wav",
            "/app/examples/voice_03.wav",
            "/app/examples/voice_04.wav",
            "/app/examples/voice_05.wav",
        ]
        self.test_text = "这是一个性能测试，用于对比不同缓存策略的速度差异。"
        self.iterations = 5
        self.results = {
            "no_cache": [],
            "disk_cache": [],
            "ram_cache": [],
            "vram_cache": []
        }
    
    def test_no_cache(self):
        """测试1: 无缓存 - 每次都重新提取embedding"""
        print("\n" + "="*60)
        print("🧪 测试1: 无缓存策略 (No Cache)")
        print("="*60)
        
        import requests
        url = "http://localhost:8002/tts"
        
        times = []
        for i in range(self.iterations):
            for speaker_idx, speaker_path in enumerate(self.test_speakers):
                print(f"\n[Round {i+1}/5] Speaker {speaker_idx+1}: {Path(speaker_path).name}")
                
                start = time.time()
                response = requests.post(url, json={
                    "text": self.test_text,
                    "spk_audio_prompt": speaker_path,
                    "disable_cache": True  # 强制禁用缓存
                })
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    times.append(elapsed)
                    print(f"  ✅ Time: {elapsed:.3f}s")
                else:
                    print(f"  ❌ Failed: {response.status_code}")
        
        self.results["no_cache"] = times
        print(f"\n📊 无缓存平均时间: {statistics.mean(times):.3f}s")
        return times
    
    def test_disk_cache(self):
        """测试2: 磁盘缓存 - 从SSD加载embedding"""
        print("\n" + "="*60)
        print("🧪 测试2: 磁盘缓存策略 (Disk Cache)")
        print("="*60)
        
        import requests
        url = "http://localhost:8002/tts_cached"
        
        # 先上传所有说话人
        print("\n📤 上传说话人到磁盘缓存...")
        speaker_ids = []
        for speaker_path in self.test_speakers:
            response = requests.post("http://localhost:8002/upload_speaker", json={
                "audio_path": speaker_path
            })
            if response.status_code == 200:
                speaker_id = response.json()["speaker_id"]
                speaker_ids.append(speaker_id)
                print(f"  ✅ {Path(speaker_path).name} -> {speaker_id}")
        
        # 测试性能
        times = []
        first_call_times = []
        subsequent_times = []
        
        for i in range(self.iterations):
            for speaker_idx, speaker_id in enumerate(speaker_ids):
                print(f"\n[Round {i+1}/5] Speaker {speaker_idx+1}: {speaker_id}")
                
                start = time.time()
                response = requests.post(url, json={
                    "text": self.test_text,
                    "speaker_id": speaker_id
                })
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    times.append(elapsed)
                    if i == 0:
                        first_call_times.append(elapsed)
                    else:
                        subsequent_times.append(elapsed)
                    print(f"  ✅ Time: {elapsed:.3f}s")
                else:
                    print(f"  ❌ Failed: {response.status_code}")
        
        self.results["disk_cache"] = {
            "all": times,
            "first_call": first_call_times,
            "subsequent": subsequent_times
        }
        print(f"\n📊 磁盘缓存平均时间: {statistics.mean(times):.3f}s")
        print(f"   - 首次调用: {statistics.mean(first_call_times):.3f}s")
        print(f"   - 后续调用: {statistics.mean(subsequent_times):.3f}s")
        return times
    
    def test_ram_cache(self):
        """测试3: 内存缓存 - 从RAM加载embedding"""
        print("\n" + "="*60)
        print("🧪 测试3: 内存缓存策略 (RAM Cache)")
        print("="*60)
        
        import requests
        url = "http://localhost:8003/tts_cached"  # 使用新端口
        
        # 先上传所有说话人
        print("\n📤 上传说话人到内存缓存...")
        speaker_ids = []
        for speaker_path in self.test_speakers:
            response = requests.post("http://localhost:8003/upload_speaker", json={
                "audio_path": speaker_path
            })
            if response.status_code == 200:
                speaker_id = response.json()["speaker_id"]
                speaker_ids.append(speaker_id)
                print(f"  ✅ {Path(speaker_path).name} -> {speaker_id}")
        
        # 测试性能
        times = []
        first_call_times = []
        subsequent_times = []
        
        for i in range(self.iterations):
            for speaker_idx, speaker_id in enumerate(speaker_ids):
                print(f"\n[Round {i+1}/5] Speaker {speaker_idx+1}: {speaker_id}")
                
                start = time.time()
                response = requests.post(url, json={
                    "text": self.test_text,
                    "speaker_id": speaker_id
                })
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    times.append(elapsed)
                    if i == 0:
                        first_call_times.append(elapsed)
                    else:
                        subsequent_times.append(elapsed)
                    print(f"  ✅ Time: {elapsed:.3f}s")
                else:
                    print(f"  ❌ Failed: {response.status_code}")
        
        self.results["ram_cache"] = {
            "all": times,
            "first_call": first_call_times,
            "subsequent": subsequent_times
        }
        print(f"\n📊 内存缓存平均时间: {statistics.mean(times):.3f}s")
        print(f"   - 首次调用: {statistics.mean(first_call_times):.3f}s")
        print(f"   - 后续调用: {statistics.mean(subsequent_times):.3f}s")
        return times
    
    def test_vram_cache(self):
        """测试4: 显存缓存 - 同一说话人连续调用（IndexTTS2原生）"""
        print("\n" + "="*60)
        print("🧪 测试4: 显存缓存策略 (VRAM Cache - Same Speaker)")
        print("="*60)
        
        import requests
        url = "http://localhost:8002/tts"
        
        # 使用同一个说话人连续调用
        speaker_path = self.test_speakers[0]
        print(f"\n使用说话人: {Path(speaker_path).name}")
        print("连续调用25次（5轮 × 5次）")
        
        times = []
        first_call_time = None
        
        for i in range(self.iterations * len(self.test_speakers)):
            print(f"\n[Call {i+1}/25]")
            
            start = time.time()
            response = requests.post(url, json={
                "text": self.test_text,
                "spk_audio_prompt": speaker_path
            })
            elapsed = time.time() - start
            
            if response.status_code == 200:
                times.append(elapsed)
                if i == 0:
                    first_call_time = elapsed
                    print(f"  ✅ Time: {elapsed:.3f}s (首次调用)")
                else:
                    print(f"  ✅ Time: {elapsed:.3f}s (显存缓存命中)")
            else:
                print(f"  ❌ Failed: {response.status_code}")
        
        subsequent_times = times[1:]
        
        self.results["vram_cache"] = {
            "all": times,
            "first_call": [first_call_time],
            "subsequent": subsequent_times
        }
        print(f"\n📊 显存缓存平均时间: {statistics.mean(times):.3f}s")
        print(f"   - 首次调用: {first_call_time:.3f}s")
        print(f"   - 后续调用: {statistics.mean(subsequent_times):.3f}s")
        return times
    
    def generate_report(self):
        """生成详细的对比报告"""
        print("\n" + "="*80)
        print("📊 四种缓存策略性能对比报告")
        print("="*80)
        
        # 计算统计数据
        report = {
            "test_config": {
                "speakers": len(self.test_speakers),
                "iterations": self.iterations,
                "total_calls": len(self.test_speakers) * self.iterations,
                "test_text": self.test_text
            },
            "results": {}
        }
        
        # 无缓存
        no_cache_times = self.results["no_cache"]
        report["results"]["no_cache"] = {
            "mean": statistics.mean(no_cache_times),
            "median": statistics.median(no_cache_times),
            "stdev": statistics.stdev(no_cache_times) if len(no_cache_times) > 1 else 0,
            "min": min(no_cache_times),
            "max": max(no_cache_times),
            "all_times": no_cache_times
        }
        
        # 磁盘缓存
        disk_all = self.results["disk_cache"]["all"]
        disk_first = self.results["disk_cache"]["first_call"]
        disk_sub = self.results["disk_cache"]["subsequent"]
        report["results"]["disk_cache"] = {
            "mean": statistics.mean(disk_all),
            "first_call_mean": statistics.mean(disk_first),
            "subsequent_mean": statistics.mean(disk_sub),
            "median": statistics.median(disk_all),
            "stdev": statistics.stdev(disk_all) if len(disk_all) > 1 else 0,
            "min": min(disk_all),
            "max": max(disk_all)
        }
        
        # 内存缓存
        ram_all = self.results["ram_cache"]["all"]
        ram_first = self.results["ram_cache"]["first_call"]
        ram_sub = self.results["ram_cache"]["subsequent"]
        report["results"]["ram_cache"] = {
            "mean": statistics.mean(ram_all),
            "first_call_mean": statistics.mean(ram_first),
            "subsequent_mean": statistics.mean(ram_sub),
            "median": statistics.median(ram_all),
            "stdev": statistics.stdev(ram_all) if len(ram_all) > 1 else 0,
            "min": min(ram_all),
            "max": max(ram_all)
        }
        
        # 显存缓存
        vram_all = self.results["vram_cache"]["all"]
        vram_first = self.results["vram_cache"]["first_call"]
        vram_sub = self.results["vram_cache"]["subsequent"]
        report["results"]["vram_cache"] = {
            "mean": statistics.mean(vram_all),
            "first_call_mean": statistics.mean(vram_first),
            "subsequent_mean": statistics.mean(vram_sub),
            "median": statistics.median(vram_all),
            "stdev": statistics.stdev(vram_all) if len(vram_all) > 1 else 0,
            "min": min(vram_all),
            "max": max(vram_all)
        }
        
        # 打印表格
        print("\n┌─────────────────┬──────────┬──────────┬──────────┬──────────┐")
        print("│ 缓存策略        │ 平均时间 │ 首次调用 │ 后续调用 │ 提升幅度 │")
        print("├─────────────────┼──────────┼──────────┼──────────┼──────────┤")
        
        baseline = report["results"]["no_cache"]["mean"]
        
        print(f"│ 无缓存          │ {report['results']['no_cache']['mean']:>6.3f}s │    -     │    -     │ 基准线   │")
        
        disk_improvement = (1 - report['results']['disk_cache']['mean'] / baseline) * 100
        print(f"│ 磁盘缓存        │ {report['results']['disk_cache']['mean']:>6.3f}s │ {report['results']['disk_cache']['first_call_mean']:>6.3f}s │ {report['results']['disk_cache']['subsequent_mean']:>6.3f}s │ {disk_improvement:>5.1f}%  │")
        
        ram_improvement = (1 - report['results']['ram_cache']['mean'] / baseline) * 100
        print(f"│ 内存缓存        │ {report['results']['ram_cache']['mean']:>6.3f}s │ {report['results']['ram_cache']['first_call_mean']:>6.3f}s │ {report['results']['ram_cache']['subsequent_mean']:>6.3f}s │ {ram_improvement:>5.1f}%  │")
        
        vram_improvement = (1 - report['results']['vram_cache']['mean'] / baseline) * 100
        print(f"│ 显存缓存(同人)  │ {report['results']['vram_cache']['mean']:>6.3f}s │ {report['results']['vram_cache']['first_call_mean']:>6.3f}s │ {report['results']['vram_cache']['subsequent_mean']:>6.3f}s │ {vram_improvement:>5.1f}%  │")
        
        print("└─────────────────┴──────────┴──────────┴──────────┴──────────┘")
        
        # 保存报告
        report_path = Path("/app/outputs/cache_benchmark_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ 详细报告已保存: {report_path}")
        
        return report


if __name__ == "__main__":
    benchmark = CacheBenchmark()
    
    print("🚀 开始四种缓存策略性能对比测试")
    print(f"📋 测试配置: {len(benchmark.test_speakers)}个说话人 × {benchmark.iterations}轮 = {len(benchmark.test_speakers) * benchmark.iterations}次调用")
    
    # 执行测试
    benchmark.test_no_cache()
    benchmark.test_disk_cache()
    benchmark.test_ram_cache()
    benchmark.test_vram_cache()
    
    # 生成报告
    benchmark.generate_report()
