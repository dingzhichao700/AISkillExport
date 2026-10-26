using System;
using System.IO;
using System.Linq;
public class TexturePackerTool {
    public static void GenerateAtlasByTexturePacker(string texturePackerPath, string sourcePath, string outputPath, float scaleRate, Action action) {
        string atlasName = Path.GetFileName(sourcePath);
        string[] files = Directory.GetFiles(sourcePath).Where(p => string.Equals(Path.GetExtension(p), ".png", StringComparison.OrdinalIgnoreCase)).ToArray();
        if (FrameAnimeExportor.AnimationBatch.Pack(texturePackerPath, files,
            Path.Combine(outputPath, atlasName + ".json"), Path.Combine(outputPath, atlasName + ".png"), scaleRate, true)) {
            action?.Invoke();
        }
    }
}
