using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using SimpleJSON;
using cfg;

// 仅替换资源 IO，编译实际 CfgManager、Helper、Luban 和生成代码。
public static class ResourceManager {
    public static string Data;
    public static JSONArray Override;
    public static JSONNode GetJsonNode(string path) {
        if (path.EndsWith("cfgobj_configvalueobj") && Override != null) return Override;
        return JSON.Parse(File.ReadAllText(Path.Combine(Data, Path.GetFileName(path) + ".json")));
    }
    public static void Release(string path) { }
}
public enum ResType { Json }
public class ResLoadInfo { public ResLoadInfo(string path, ResType type) { } }
public static class ResourceLoader { public static Task LoadListAsync(List<ResLoadInfo> items, int maxConcurrent) => Task.CompletedTask; }
public static class LoadTiming {
    public static Task MeasureAsync(string name, Func<Task> operation) => operation();
    public static void Report(string name, System.Diagnostics.Stopwatch watch) { }
}
public static class ConfigValueRegression {
    private static int passed;
    private static void Check(bool value, string name) {
        if (!value) throw new Exception(name);
        passed++;
    }
    private static void Throws<T>(Action action) where T : Exception {
        try { action(); } catch (T) { passed++; return; }
        throw new Exception("Expected " + typeof(T).Name);
    }
    private static void Replace(int id, string content) {
        foreach (JSONNode row in ResourceManager.Override) {
            if (row["id"].AsInt == id) row["content"] = content;
        }
        CfgManager.Init();
    }
    public static void Main(string[] args) {
        ResourceManager.Data = args[0];
        CfgManager.Init();
        for (int id = 1; id <= 8; id++) Check(CfgManager.tables.ConfigValueObj.GetOrDefault(id) != null, "missing sample " + id);
        var errors = new List<Exception>();
        foreach (var row in CfgManager.tables.ConfigValueObj.DataList) {
            try {
                if (row.Id == 2) { Throws<OverflowException>(() => ConfigValueHelper.GetInt(2)); continue; }
                object value;
                if (row.Type == ConfigValueType.NORMAL) {
                    switch (row.ValueType) {
                        case ConfigValueFormat.INT: value = ConfigValueHelper.GetInt(row.Id); break;
                        case ConfigValueFormat.FLOAT: value = ConfigValueHelper.GetFloat(row.Id); break;
                        case ConfigValueFormat.STRING: value = ConfigValueHelper.GetString(row.Id); break;
                        default: throw new Exception("Unknown value format");
                    }
                } else if (row.Type == ConfigValueType.LIST) {
                    switch (row.ValueType) {
                        case ConfigValueFormat.INT: value = string.Join(",", ConfigValueHelper.GetList<int>(row.Id)); break;
                        case ConfigValueFormat.FLOAT: value = string.Join(",", ConfigValueHelper.GetList<float>(row.Id)); break;
                        case ConfigValueFormat.STRING: value = string.Join(",", ConfigValueHelper.GetList<string>(row.Id)); break;
                        default: throw new Exception("Unknown value format");
                    }
                } else if (row.Type == ConfigValueType.MAP) {
                    switch (row.ValueType) {
                        case ConfigValueFormat.INT: value = string.Join(",", ConfigValueHelper.GetMap<int>(row.Id)); break;
                        case ConfigValueFormat.FLOAT: value = string.Join(",", ConfigValueHelper.GetMap<float>(row.Id)); break;
                        case ConfigValueFormat.STRING: value = string.Join(",", ConfigValueHelper.GetMap<string>(row.Id)); break;
                        default: throw new Exception("Unknown value format");
                    }
                } else throw new Exception("Unknown structure");
                Console.WriteLine("Config " + row.Id + ": " + value);
            } catch (Exception error) { errors.Add(error); }
        }
        if (errors.Count > 0) throw new AggregateException(errors);
        var list = ConfigValueHelper.GetList<int>(6);
        Check(ReferenceEquals(list, ConfigValueHelper.GetList<int>(6)), "cache reuse");
        Throws<InvalidOperationException>(() => ConfigValueHelper.GetList<float>(6));
        Throws<NotSupportedException>(() => ConfigValueHelper.GetList<double>(6));
        Throws<NotSupportedException>(() => ((IList<int>)list)[0] = 0);
        Throws<NotSupportedException>(() => ((IDictionary<string,string>)ConfigValueHelper.GetMap<string>(8)).Add("x", "y"));
        Throws<KeyNotFoundException>(() => ConfigValueHelper.GetInt(-1));
        CfgManager.Init();
        Check(!ReferenceEquals(list, ConfigValueHelper.GetList<int>(6)), "Init clears cache");
        list = ConfigValueHelper.GetList<int>(6);
        CfgManager.Clear();
        Throws<InvalidOperationException>(() => ConfigValueHelper.GetList<int>(6));
        CfgManager.Init();
        Check(!ReferenceEquals(list, ConfigValueHelper.GetList<int>(6)), "Clear reload");
        ResourceManager.Override = JSON.Parse(File.ReadAllText(Path.Combine(args[0], "cfgobj_configvalueobj.json"))).AsArray;
        Replace(7, @"a\,b,c\\d,");
        Check(ConfigValueHelper.GetList<string>(7)[0] == "a,b" && ConfigValueHelper.GetList<string>(7)[2] == "", "escaped list");
        Replace(8, @"a\:b:hello\,world");
        Check(ConfigValueHelper.GetMap<string>(8)["a:b"] == "hello,world", "escaped map");
        Replace(8, "a:1,a:2"); Throws<FormatException>(() => ConfigValueHelper.GetMap<string>(8));
        Replace(7, @"bad\q"); Throws<FormatException>(() => ConfigValueHelper.GetList<string>(7));
        Replace(3, "NaN"); Throws<OverflowException>(() => ConfigValueHelper.GetFloat(3));
        Replace(6, ""); Check(ConfigValueHelper.GetList<int>(6).Count == 0, "empty list");
        Replace(2, "17"); Check(ConfigValueHelper.GetInt(2) == 17, "failed parse not retained");
        CfgManager.Clear();
        Console.WriteLine("PASS ConfigValue checks=" + passed);
    }
}
