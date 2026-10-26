using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace FrameAnimeExportor {
    internal static class AnimationBatch {
        public static int FrameDuration(int total, int count, int index) {
            return (int)((long)total * index / count - (long)total * (index - 1) / count);
        }

        public static bool Pack(string executable, string[] files, string json, string png, float scale, bool square) {
            string args = "--texture-format png8 --format json-array --size-constraints POT " +
                (square ? "--force-squared " : "") + "--max-size 2048 --trim-mode Trim --disable-rotation --algorithm MaxRects --extrude 0 --scale " +
                scale.ToString(CultureInfo.InvariantCulture) + " --data " + Quote(json) + " --sheet " + Quote(png) + " " +
                string.Join(" ", files.Select(Quote));
            Console.WriteLine("TexturePacker: " + args);
            using (var process = new Process()) {
                process.StartInfo = new ProcessStartInfo(executable, args) {
                    UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardOutput = true, RedirectStandardError = true
                };
                process.OutputDataReceived += (s, e) => { if (e.Data != null) Console.WriteLine(e.Data); };
                process.ErrorDataReceived += (s, e) => { if (e.Data != null) Console.Error.WriteLine(e.Data); };
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                process.WaitForExit();
                return process.ExitCode == 0;
            }
        }

        private static string Quote(string value) { return "\"" + value + "\""; }

        public static int Run(string[] args) {
            try {
                if (args.Length == 1 && (args[0] == "--help" || args[0] == "help")) {
                    Console.WriteLine("pack --input <directory> --output <directory> --texture-packer <exe> [--square] [--overwrite]\nReads animation.json and numbered PNGs. duration: milliseconds; scale: percent (default 100); pivot: bottom-left origin. Exit: 0 success, 1 arguments, 2 batch failure.");
                    return 0;
                }
                if (args[0] != "pack") throw new ArgumentException("Expected pack or --help.");
                var options = new Dictionary<string, string>();
                for (int i = 1; i < args.Length; i++) {
                    string key = args[i];
                    if (options.ContainsKey(key)) throw new ArgumentException("Duplicate option: " + key);
                    if (key == "--square" || key == "--overwrite") options.Add(key, "true");
                    else if (key == "--input" || key == "--output" || key == "--texture-packer") {
                        if (++i >= args.Length) throw new ArgumentException("Missing value: " + key);
                        options.Add(key, args[i]);
                    } else throw new ArgumentException("Unknown option: " + key);
                }
                foreach (string key in new[] { "--input", "--output", "--texture-packer" })
                    if (!options.ContainsKey(key)) throw new ArgumentException("Required: " + key);
                string input = Path.GetFullPath(options["--input"]).TrimEnd(Path.DirectorySeparatorChar);
                string output = Path.GetFullPath(options["--output"]).TrimEnd(Path.DirectorySeparatorChar);
                string exe = Path.GetFullPath(options["--texture-packer"]);
                if (!Directory.Exists(input) || !File.Exists(exe)) throw new ArgumentException("Input directory or TexturePacker does not exist.");
                if (output.Equals(input, StringComparison.OrdinalIgnoreCase) || output.StartsWith(input + "\\", StringComparison.OrdinalIgnoreCase))
                    throw new ArgumentException("Output must be outside input directory.");
                string[] configs = Directory.GetFiles(input, "animation.json", SearchOption.AllDirectories).OrderBy(p => p, StringComparer.OrdinalIgnoreCase).ToArray();
                if (configs.Length == 0) throw new ArgumentException("No animation.json found.");
                int failed = 0;
                foreach (string config in configs) {
                    try {
                        Export(config, input, output, exe, options.ContainsKey("--square"), options.ContainsKey("--overwrite"));
                    } catch (Exception error) {
                        failed++;
                        Console.Error.WriteLine("FAIL " + config + ": " + error.Message);
                    }
                }
                Console.WriteLine("SUMMARY success=" + (configs.Length - failed) + " failed=" + failed);
                return failed == 0 ? 0 : 2;
            } catch (Exception error) {
                Console.Error.WriteLine(error.Message);
                return 1;
            }
        }

        private static double Number(JToken token, string name, double min, double max) {
            if (token == null || (token.Type != JTokenType.Integer && token.Type != JTokenType.Float))
                throw new InvalidDataException(name + " must be numeric.");
            double value = token.Value<double>();
            if (double.IsNaN(value) || double.IsInfinity(value) || value < min || value > max)
                throw new InvalidDataException(name + " out of range.");
            return value;
        }

        private static void Export(string config, string root, string output, string exe, bool square, bool overwrite) {
            string directory = Path.GetDirectoryName(config);
            var settings = JObject.Parse(File.ReadAllText(config, new UTF8Encoding(false, true)));
            string[] files = Directory.GetFiles(directory, "*.png").Where(p => Regex.IsMatch(Path.GetFileNameWithoutExtension(p), @"^\d+$"))
                .OrderBy(p => long.Parse(Path.GetFileNameWithoutExtension(p), CultureInfo.InvariantCulture)).ToArray();
            if (files.Length == 0) throw new InvalidDataException("No numbered PNG frames.");
            int digits = Path.GetFileNameWithoutExtension(files[0]).Length;
            int width = 0, height = 0;
            for (int i = 0; i < files.Length; i++) {
                if (Path.GetFileNameWithoutExtension(files[i]) != (i + 1).ToString("D" + digits))
                    throw new InvalidDataException("Frame numbering must be continuous from 1 with equal padding.");
                using (var image = System.Drawing.Image.FromFile(files[i])) {
                    if (i == 0) { width = image.Width; height = image.Height; }
                    if (image.Width != width || image.Height != height) throw new InvalidDataException("Frame dimensions differ.");
                }
            }
            if (settings["duration"] == null || settings["duration"].Type != JTokenType.Integer) throw new InvalidDataException("duration must be integer milliseconds.");
            int duration = (int)Number(settings["duration"], "duration", files.Length, int.MaxValue);
            float scale = (float)(settings["scale"] == null ? 1 : Number(settings["scale"], "scale", 10, 200) / 100);
            double x = Number(settings["pivot"]?["x"], "pivot.x", 0, 1);
            double y = Number(settings["pivot"]?["y"], "pivot.y", 0, 1);
            string relative = directory.Equals(root, StringComparison.OrdinalIgnoreCase) ? Path.GetFileName(directory) : directory.Substring(root.Length + 1);
            string destination = Path.Combine(output, relative);
            if (!overwrite && (File.Exists(destination + ".json") || File.Exists(destination + ".png")))
                throw new IOException("Output exists; use --overwrite explicitly.");
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            //隔离中间产物，失败时不将 TexturePacker 原始 JSON 当成最终动画 JSON。
            string staging = Path.Combine(Path.GetDirectoryName(destination), ".pack-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(staging);
            try {
                string json = Path.Combine(staging, Path.GetFileName(destination) + ".json");
                string png = Path.ChangeExtension(json, ".png");
                if (!Pack(exe, files, json, png, scale, square)) throw new IOException("TexturePacker failed.");
                var result = JObject.Parse(File.ReadAllText(json));
                var frames = (JArray)result["frames"];
                if (frames == null || frames.Count != files.Length || !File.Exists(png)) throw new InvalidDataException("Missing output or frame count mismatch.");
                var ordered = frames.OrderBy(f => long.Parse(Path.GetFileNameWithoutExtension((string)f["filename"]))).ToArray();
                for (int i = 0; i < ordered.Length; i++) {
                    if (Path.GetFileName((string)ordered[i]["filename"]) != Path.GetFileName(files[i])) throw new InvalidDataException("Output frame names mismatch.");
                    ordered[i]["duration"] = FrameDuration(duration, files.Length, i + 1);
                }
                result["frames"] = new JArray(ordered);
                //沿用现有 UI 导出格式：pivot 数值以字符串保存。
                result["pivot"] = new JObject { ["x"] = x.ToString(CultureInfo.InvariantCulture), ["y"] = y.ToString(CultureInfo.InvariantCulture) };
                result["meta"] = null;
                File.WriteAllText(json, result.ToString(Formatting.None), new UTF8Encoding(false));
                File.Copy(png, destination + ".png", overwrite);
                File.Copy(json, destination + ".json", overwrite);
                Console.WriteLine("OK " + relative + " frames=" + files.Length + " duration=" + duration);
            } finally {
                foreach (string file in Directory.GetFiles(staging)) File.Delete(file);
                Directory.Delete(staging);
            }
        }
    }
}
