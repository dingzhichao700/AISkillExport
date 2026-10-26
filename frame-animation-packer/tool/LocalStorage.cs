using Newtonsoft.Json;
using System.Collections.Generic;
using System.IO;

namespace FrameAnimeExportor
{
    /// <summary>
    /// 本地化缓存
    /// </summary>
    class LocalStorage
    {
        private static Dictionary<string, string> cacheMap;

        private const string PATH_CACHE = "localStorage.json";

        private static void Init()
        {
            // 读取JSON文件内容
            if (File.Exists(PATH_CACHE))
            {
                string jsonCache = File.ReadAllText(PATH_CACHE);
                // 反序列化JSON到List
                //cache = JsonConvert.DeserializeObject<List<string>>(jsonCache);
                // 反序列化JSON到字典
                cacheMap = JsonConvert.DeserializeObject<Dictionary<string, string>>(jsonCache);
            }
            else
            {
                cacheMap = new Dictionary<string, string>();
            }
        }

        // 取数据
        public static string GetKey(string key)
        {
            if (cacheMap == null)
            {
                Init();
            }
            string valueStr;
            if (cacheMap.TryGetValue(key, out valueStr))
            {
                return valueStr;
            }
            return null;
        }

        //写入数据并存储
        public static void SetKey(string key, string value)
        {
            if (cacheMap == null)
            {
                Init();
            }
            cacheMap[key] = value;
            SaveToFile();
        }

        //保存到文件
        private static void SaveToFile()
        {
            // 序列化到JSON并保存到文件
            string jsonCache = JsonConvert.SerializeObject(cacheMap, Formatting.Indented);
            File.WriteAllText(PATH_CACHE, jsonCache);
        }

    }
}
