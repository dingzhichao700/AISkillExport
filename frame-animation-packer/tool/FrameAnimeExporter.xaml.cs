using Microsoft.WindowsAPICodePack.Dialogs;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Text.RegularExpressions;
using System.Timers;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using static System.Environment;

namespace FrameAnimeExportor {
    /// <summary>
    /// MainWindow.xaml 的交互逻辑
    /// </summary>
    public partial class MainWindow : Window {

        //总帧数
        private int frameNum;

        //总时长
        private int durationTotal = 1000;

        //帧item列表
        private List<UI.FrameItem> frameItems;

        //每帧时长map<帧索引，帧时长>
        private Dictionary<int, int> frameDurationMap;

        //文件路径：TexturePacker.exe
        private string pathForTexturePacker;
        //文件路径：序列帧png
        private string pathForFrames;
        //文件路径：输出目录
        private string pathForOutput;
        //帧动画名称
        private string actionName;

        /**图集json信息*/
        private JToken token;
        /**从图集json中读取出的帧信息*/
        private JArray atlasFrames;
        /**加载用的图片对象*/
        private Image loadImage;
        /**当前是否播放中*/
        private bool isPlaying;
        /**当前播放时刻*/
        private long playDuration;

        /**缩放值*/
        private double scaleValue = 1;
        private double anchorX;
        private double anchorY;

        //缓存key:TexturePacker路径
        private const string CACHE_KEY_PATH_TEXTURE_PACKER = "CACHE_KEY_PATH_TEXTURE_PACKER";
        //缓存key:输出路径
        private const string CACHE_KEY_PATH_OUT_PUT = "CACHE_KEY_PATH_OUT_PUT";

        public MainWindow() {
            InitializeComponent();

            txtDuration.Text = durationTotal + "";
            MainControl.ins.SetMainView(this);
            pathForTexturePacker = LocalStorage.GetKey(CACHE_KEY_PATH_TEXTURE_PACKER);
            pathForOutput = LocalStorage.GetKey(CACHE_KEY_PATH_OUT_PUT);
            Update();
        }

        private void Update() {
            txtTexturePacker.Text = "TexturePacker.exe路径：" + pathForTexturePacker;
            txtTexturePacker.Foreground = pathForTexturePacker == null ? new SolidColorBrush(Colors.Red) : new SolidColorBrush(Colors.Black);

            txtInputPath.Text = "序列帧路径：" + pathForFrames;
            txtInputPath.Foreground = pathForFrames == null ? new SolidColorBrush(Colors.Red) : new SolidColorBrush(Colors.Black);

            txtOutputPath.Text = "输出路径：" + pathForOutput;
            txtOutputPath.Foreground = pathForOutput == null ? new SolidColorBrush(Colors.Red) : new SolidColorBrush(Colors.Black);

            btnExploreToTexturePacker.Visibility = pathForTexturePacker == null ? Visibility.Hidden : Visibility.Visible;
            btnExploreToFrames.Visibility = pathForFrames == null ? Visibility.Hidden : Visibility.Visible;
            btnExploreToOutput.Visibility = pathForOutput == null ? Visibility.Hidden : Visibility.Visible;
        }

        //设置打图集工具TexturePacker.exe的路径
        private void OnSetTexturePackerPath(object sender, RoutedEventArgs e) {
            //选择文件
            Microsoft.Win32.OpenFileDialog openFileDialog = new Microsoft.Win32.OpenFileDialog();
            openFileDialog.DefaultExt = ".exe";
            openFileDialog.Multiselect = true;
            openFileDialog.Filter = "TexturePacker Tool|*.exe";
            if (openFileDialog.ShowDialog() == true) {
                string filename = openFileDialog.FileName;
                pathForTexturePacker = filename;
                LocalStorage.SetKey(CACHE_KEY_PATH_TEXTURE_PACKER, filename);
                Update();
            }
        }

        /**导入序列帧*/
        private void OnImportFrames(object sender, RoutedEventArgs e) {
            if (pathForTexturePacker == null) {
                MessageBox.Show("请先设置TexturePacker.exe路径");
                return;
            }
            if (pathForOutput == null) {
                MessageBox.Show("请先设置输出路径");
                return;
            }

            //选择文件夹
            var dialog = new CommonOpenFileDialog {
                IsFolderPicker = true,  // 👈 设置为选择文件夹
                Title = "请选择文件夹"
            };

            if (dialog.ShowDialog() == CommonFileDialogResult.Ok) {
                pathForFrames = dialog.FileName;
                Update();

                //先删除一次图集的图片和json
                //int lastSplit = pathForFrames.LastIndexOf("\\");
                //frameName = pathForFrames.Substring(lastSplit, (pathForFrames.Length - lastSplit));
                //if (File.Exists(pathForFrames + frameName + ".json")) {
                //    File.Delete(pathForFrames + frameName + ".json");
                //}
                //if (File.Exists(pathForFrames + frameName + ".png")) {
                //    File.Delete(pathForFrames + frameName + ".png");
                //}

                //TexturePackerTool.GenerateAtlasByTexturePacker(pathForTexturePacker, pathForFrames, OnGenerateAtlasComplete);
                //先删除一次图集的图片和json
                int lastSplit = pathForFrames.LastIndexOf("\\");
                actionName = pathForFrames.Substring(lastSplit, (pathForFrames.Length - lastSplit));
                if (File.Exists(pathForOutput + actionName + ".json")) {
                    File.Delete(pathForOutput + actionName + ".json");
                }
                if (File.Exists(pathForOutput + actionName + ".png")) {
                    File.Delete(pathForOutput + actionName + ".png");
                }
                PackFrameImages();
            }
        }

        private void PackFrameImages() {
            TexturePackerTool.GenerateAtlasByTexturePacker(pathForTexturePacker, pathForFrames, pathForOutput, (float)scaleValue, OnGenerateAtlasComplete);
        }

        //图集生成完成
        private void OnGenerateAtlasComplete() {
            OnReadJson(pathForOutput + actionName + ".json");
            OnReadImage(pathForOutput + actionName + ".png");

            //图集的json和图片都读取好了，选中首帧
            MainControl.ins.SetFocusFrame(1);
        }

        //设置输出路径
        private void OnSetOutputPath(object sender, RoutedEventArgs e) {
            //选择文件夹
            System.Windows.Forms.FolderBrowserDialog folderBrowserDialog = new System.Windows.Forms.FolderBrowserDialog();
            folderBrowserDialog.RootFolder = SpecialFolder.Desktop;
            if (folderBrowserDialog.ShowDialog() == System.Windows.Forms.DialogResult.OK) {
                string directoryPath = folderBrowserDialog.SelectedPath;
                pathForOutput = directoryPath;
                LocalStorage.SetKey(CACHE_KEY_PATH_OUT_PUT, directoryPath);
                Update();
            }
        }

        //读json
        private void OnReadJson(string jsonPath) {
            string jsonContent = File.ReadAllText(jsonPath);
            Console.WriteLine(jsonContent);

            token = JToken.Parse(jsonContent);
            atlasFrames = token["frames"] as JArray;

            //先生成对应数量的时间轴帧item
            GenerateTimelineContent(atlasFrames.Count);
            //再按当前总时长平均划分一次每帧的时长
            DurationAveragetion();
        }

        /**输入总时长*/
        private void txtDuration_KeyUp(object sender, KeyEventArgs e) {
            //txtInputPath.Text = "动画时长：" + txtDuration.Text;
            if (e.Key != Key.Enter) {
                return;
            }
            int inputDuration;
            int minDuration = Math.Max(1, frameNum);
            if (!int.TryParse(txtDuration.Text, out inputDuration) || inputDuration < minDuration) {
                txtDuration.Text = durationTotal.ToString();
                MessageBox.Show($"总播放时长必须是至少 {minDuration} 毫秒的整数，保证每帧至少 1 毫秒");
                return;
            }
            durationTotal = inputDuration;
            if (frameNum > 0) {
                DurationAveragetion();
            }
        }

        /// <summary>
        /// 基于总时长平均划分一下每帧时长
        /// </summary>
        private void DurationAveragetion() {
            frameDurationMap = new Dictionary<int, int>();
            if (frameNum <= 0) {
                return;
            }

            //重新导入更多帧时，自动补足到每帧至少 1 毫秒
            durationTotal = Math.Max(durationTotal, frameNum);
            txtDuration.Text = durationTotal.ToString();
            for (int i = 1; i <= frameNum; i++) {
                frameDurationMap[i] = AnimationBatch.FrameDuration(durationTotal, frameNum, i);
            }
            UpdateLayoutTimelineFrames();
        }

        /**获取某时刻对应的帧序号*/
        private int GetIndexByTime(long time) {
            int result = 1;
            int totalTime = 0;
            for (int i = 1; i <= frameItems.Count; i++) {
                totalTime += frameDurationMap[i];
                if (time <= totalTime) {
                    result = i;
                    break;
                }
            }
            return result;
        }

        //文本预输入处理
        private void PreviewTextInput(object sender, TextCompositionEventArgs e) {
            //让部分文本输入框只能输入数字和一个小数点
            if (new Regex("[^0-9.]+").IsMatch(e.Text)) {
                e.Handled = true;
                return;
            }

            var textBox = sender as System.Windows.Controls.TextBox;
            if (textBox != null && e.Text.Contains(".")) {
                string selectedText = textBox.SelectedText;
                bool selectedExistingDot = selectedText.Contains(".");
                e.Handled = textBox.Text.Contains(".") && !selectedExistingDot;
            }
        }

        private void TextBlock_KeyUp(object sender, KeyEventArgs e) {

        }

        /// <summary>
        /// 生成时间轴内容
        /// </summary>
        /// <param name="itemCount"></param>
        private void GenerateTimelineContent(int itemCount) {
            ClearTimeline();
            frameNum = itemCount;
            frameItems = new List<UI.FrameItem>();
            for (int i = 0; i < frameNum; i++) {
                var frameItem = new UI.FrameItem();
                frameItem.SetIndex(i + 1);
                frameItems.Add(frameItem);
                stackTimeline.Children.Add(frameItem);
            }
        }

        private void OnReadImage(string imagePath) {
            using (Image img = Image.FromFile(imagePath)) {
                loadImage = new Bitmap(img); // 完全复制到内存
            }
        }

        private BitmapImage LoadUnlocked(string path) {
            var bi = new BitmapImage();
            bi.BeginInit();
            bi.CacheOption = BitmapCacheOption.OnLoad; // 关键：一次性加载到内存
            bi.UriSource = new Uri(path);
            bi.EndInit();
            bi.Freeze(); // 使其可跨线程且不再触摸底层流
            return bi;
        }
        // 使用：image.Source = LoadUnlocked(path);


        /// <summary>
        /// 绘制帧
        /// </summary>
        /// <param name="index">帧序号，从1开始</param>
        private void PaintFrame(int index) {
            JObject frameItem = atlasFrames[index - 1] as JObject;
            JObject frame = frameItem["frame"] as JObject;
            JObject sourceSize = frameItem["sourceSize"] as JObject;
            JObject spriteSourceSize = frameItem["spriteSourceSize"] as JObject;

            /**图片原始高度*/
            int originWidth = sourceSize.Value<int>("w");
            /**图片原始宽度*/
            int originHeight = sourceSize.Value<int>("h");
            /**从图集的哪里开始绘制X*/
            int pivotXfromAtlas = frame.Value<int>("x");
            /**从图集的哪里开始绘制Y*/
            int pivotYfromAtlas = frame.Value<int>("y");
            /**获取内容后绘制到自身的哪个位置X*/
            int destX = spriteSourceSize.Value<int>("x");
            /**获取内容后绘制到自身的哪个位置Y*/
            int destY = spriteSourceSize.Value<int>("y");
            /**内容宽度（裁剪透明像素后的）*/
            int contentWidth = frame.Value<int>("w");
            /**内容高度（裁剪透明像素后的）*/
            int contentHeight = frame.Value<int>("h");

            Bitmap bitmap = new Bitmap(originWidth, originHeight);
            Graphics graph = Graphics.FromImage(bitmap);

            graph.Clear(System.Drawing.Color.Transparent);

            //执行裁剪操作
            graph.DrawImage(loadImage, new Rectangle(destX, destY, contentWidth, contentHeight), new Rectangle(pivotXfromAtlas, pivotYfromAtlas, contentWidth, contentHeight), GraphicsUnit.Pixel);

            //绘制一下区域边框
            if ((bool)checkboxFrame.IsChecked) {
                graph.DrawRectangle(new System.Drawing.Pen(System.Drawing.Color.Yellow), new Rectangle(0, 0, originWidth - 1, originHeight - 1));
                graph.DrawRectangle(new System.Drawing.Pen(System.Drawing.Color.Green), new Rectangle(destX, destY, contentWidth, contentHeight));
            }

            MemoryStream memoryStream = new MemoryStream();
            bitmap.Save(memoryStream, ImageFormat.Png);
            memoryStream.Position = 0;
            BitmapImage bitmapImage = new BitmapImage();
            bitmapImage.BeginInit();
            bitmapImage.StreamSource = memoryStream;
            bitmapImage.CacheOption = BitmapCacheOption.OnLoad;
            bitmapImage.EndInit();
            bitmapImage.Freeze();
            imgFrame.Width = bitmap.Width;
            imgFrame.Height = bitmap.Height;
            imgFrame.Source = bitmapImage;

            UpdateLayoutFrame();
        }

        //布局当前帧
        private void UpdateLayoutFrame() {
            imgFrame.Margin = new Thickness(canvasFrame.ActualWidth / 2 - imgFrame.Width / 2, (stackScene.ActualHeight - gridTimeline.ActualHeight) / 2 - imgFrame.Height / 2, 0, 0);
            UpdateAnchorImage();
        }

        //布局时间轴的帧item
        private void UpdateLayoutTimelineFrames() {
            if (frameItems != null) {
                double widthTotal = Math.Floor(gridTimeline.ActualWidth);
                for (int i = 0; i < frameItems.Count; i++) {
                    int duration = frameDurationMap[i + 1];
                    double ratio = (double)duration / durationTotal;
                    (frameItems[i] as UI.FrameItem).Width = ratio * widthTotal;
                    (frameItems[i] as UI.FrameItem).SetDuration(frameDurationMap[i + 1]);
                }
            }
        }

        /// <summary>
        /// 设置某帧时长
        /// </summary>
        /// <param name="index">帧索引</param>
        /// <param name="duration">帧时长</param>
        public void SetFrameDuration(int index, int duration) {
            frameDurationMap[index] = duration;
            int totalTime = 0;
            foreach (int frameIndex in frameDurationMap.Keys) {
                totalTime += frameDurationMap[frameIndex];
            }
            durationTotal = totalTime;
            txtDuration.Text = totalTime + "";
            UpdateLayoutTimelineFrames();
        }

        //鼠标在时间轴某帧上按下
        public void MouseDownFrame(int index) {
            PaintFrame(index);
        }

        private void ClearTimeline() {
            stackTimeline.Children.RemoveRange(0, stackTimeline.Children.Count);
        }

        /**窗口尺寸变化*/
        private void Grid_SizeChanged(object sender, SizeChangedEventArgs e) {
            //Console.WriteLine("gridTimeline Width:" + gridTimeline.ActualWidth);
            UpdateLayoutTimelineFrames();
            UpdateLayoutFrame();
        }

        private void btnExploreToTexturePackerHandler(object sender, RoutedEventArgs e) {
            string folderPath = pathForTexturePacker.Substring(0, pathForTexturePacker.LastIndexOf("\\"));
            ExploreToDirectory(folderPath);
        }

        private void btnExploreToFramesHandler(object sender, RoutedEventArgs e) {
            ExploreToDirectory(pathForFrames);
        }

        private void btnExploreToOutputHandler(object sender, RoutedEventArgs e) {
            ExploreToDirectory(pathForOutput);
        }

        //打开到文件夹
        private void ExploreToDirectory(string path) {
            if (!Directory.Exists(path)) {
                MessageBox.Show("指定的文件夹不存在。");
                return;
            }
            Process.Start("explorer.exe", path);
        }

        private Timer timer;
        private long lastTimeStep;

        //播放
        private void btnPlay_Click(object sender, RoutedEventArgs e) {
            if (!isPlaying) {
                if (atlasFrames == null) {
                    MessageBox.Show("加载图集才能播放");
                    return;
                }
                //播放
                if (timer == null) {
                    //设置定时间隔(毫秒为单位)
                    timer = new System.Timers.Timer(10);
                    //设置执行一次（false）还是一直执行(true)
                    timer.AutoReset = true;
                    //设置是否执行System.Timers.Timer.Elapsed事件
                    timer.Enabled = true;
                    //绑定Elapsed事件
                    timer.Elapsed += new ElapsedEventHandler(OnAnimeLoop);
                }
                lastTimeStep = DateTimeOffset.Now.ToUnixTimeMilliseconds();
                playDuration = 0;
                isPlaying = true;
                timer.Start();
                btnPlay.Content = "暂停";
            } else {
                //暂停
                if (timer != null) {
                    timer.Stop();
                }
                isPlaying = false;
                btnPlay.Content = "播放";
            }
        }

        /**当前是否循环播放*/
        public bool IsLoop() {
            return (bool)checkboxLoop.IsChecked;
        }

        //帧频函数
        private void OnAnimeLoop(object sender, ElapsedEventArgs e) {
            long curTimestep = DateTimeOffset.Now.ToUnixTimeMilliseconds();
            if (isPlaying) {
                long passTime = curTimestep - lastTimeStep;
                playDuration += passTime;

                Application.Current.Dispatcher.Invoke(() => {
                    if (MainControl.ins.IsLoop()) {
                        //循环播放
                        if (playDuration > durationTotal) {
                            playDuration = playDuration % durationTotal;
                        }
                    } else {
                        //不循环播放
                        if (playDuration > durationTotal) {
                            playDuration = durationTotal;
                            isPlaying = false;
                            //btnPlay.Content = "播放";
                            return;
                        }
                    }
                    int frameIndex = GetIndexByTime(playDuration);
                    MainControl.ins.SetFocusFrame(frameIndex);
                    //PaintFrame(frameIndex);
                    //Console.WriteLine("passTime:" + passTime + ", playDuration:" + playDuration+", curTimestep:" + curTimestep);
                    Console.WriteLine("playDuration:" + playDuration + ", frameIndex:" + frameIndex);
                });
            }
            lastTimeStep = curTimestep;
        }

        /**点击重新导入*/
        private void btnReimport_Click(object sender, RoutedEventArgs e) {
            if (pathForTexturePacker == null) {
                MessageBox.Show("请先设置TexturePacker.exe路径");
                return;
            }
            if (pathForOutput == null) {
                MessageBox.Show("请先设置输出路径");
                return;
            }
            if (pathForFrames == null) {
                MessageBox.Show("请先选择帧动画路径");
                return;
            }
            PackFrameImages();
        }

        /**导出*/
        private void btnExport_Click(object sender, RoutedEventArgs e) {
            if (atlasFrames == null) {
                MessageBox.Show("请先导入序列帧资源");
                return;
            }

            //动态调整及增加字段到JObject对象中
            for (int i = 0; i < atlasFrames.Count; i++) {
                JObject firstOne = atlasFrames[i] as JObject;
                firstOne["duration"] = frameDurationMap[i + 1];
            }
            token["frames"] = atlasFrames;

            JObject pivot = new JObject();
            pivot.Add("x", txtAnchorX.Text);
            pivot.Add("y", txtAnchorY.Text);
            token["pivot"] = pivot;

            token["meta"] = null;

            // 序列化到JSON并保存到文件
            string jsonCache = JsonConvert.SerializeObject(token, Formatting.None);
            File.WriteAllText(pathForOutput + "\\" + actionName + ".json", jsonCache);

            MessageBox.Show("导出完成");
        }

        /**缩放值文本框*/
        private void txtScale_KeyUp(object sender, KeyEventArgs e) {
            if (e.Key != Key.Enter) {
                return;
            }

            float inputScale;
            if (!float.TryParse(txtScale.Text, out inputScale)) {
                txtScale.Text = scaleValue + "";
                MessageBox.Show("请输入0.1到2.0之间的有效缩放值");
                return;
            }

            scaleValue = Math.Min(Math.Max(inputScale, 0.1f), 2.0f);
            txtScale.Text = scaleValue + "";
        }

        private void sliderAnchorX_DragDelta(object sender, System.Windows.Controls.Primitives.DragDeltaEventArgs e) {
            double value = Math.Round(sliderAnchorX.Value, 2);
            //Console.WriteLine("valueX:" + value);
            txtAnchorX.Text = value + "";
            anchorX = value;
            UpdateAnchorImage();
        }

        private void sliderAnchorY_DragDelta(object sender, System.Windows.Controls.Primitives.DragDeltaEventArgs e) {
            double value = Math.Round(sliderAnchorY.Value, 2);
            txtAnchorY.Text = value + "";
            anchorY = value;
            UpdateAnchorImage();
        }

        private void txtAnchorX_KeyUp(object sender, KeyEventArgs e) {
            if (e.Key != Key.Enter) {
                return;
            }
            float value = Math.Min(Math.Max(float.Parse(txtAnchorX.Text), 0), 1.0f);
            txtAnchorX.Text = value + "";
            sliderAnchorX.Value = anchorX = value;
            UpdateAnchorImage();
        }

        private void txtAnchorY_KeyUp(object sender, KeyEventArgs e) {
            if (e.Key != Key.Enter) {
                return;
            }
            float value = Math.Min(Math.Max(float.Parse(txtAnchorY.Text), 0), 1.0f);
            txtAnchorY.Text = value + "";
            sliderAnchorY.Value = anchorY = value;
            UpdateAnchorImage();
        }

        /**更新锚点图标坐标*/
        private void UpdateAnchorImage() {
            if (atlasFrames == null) {
                return;
            }
            double left = canvasFrame.ActualWidth / 2 - imgFrame.Width / 2 + imgFrame.Width * anchorX - imgAnchor.Width / 2;
            double top = (stackScene.ActualHeight - gridTimeline.ActualHeight) / 2 + imgFrame.Height * (0.5 - anchorY) - imgAnchor.Height / 2;
            imgAnchor.Margin = new Thickness(left, top, 0, 0);
        }

        /**是否正在拖动锚点*/
        private bool isDragingAnchor;

        /**锚点被开始拖动的坐标点*/
        private System.Windows.Point dragBeginPoint;
        private Thickness dragBeginMargin;

        /**锚点上按下*/
        private void imgAnchor_MouseDown(object sender, MouseButtonEventArgs e) {
            if (atlasFrames == null) {
                return;
            }
            isDragingAnchor = true;
            dragBeginPoint = e.GetPosition(this);
            dragBeginMargin = imgAnchor.Margin;
            //Console.WriteLine("drag start");
        }

        /**锚点拖动*/
        private void grid_MouseMove(object sender, MouseEventArgs e) {
            if (isDragingAnchor) {
                System.Windows.Point pt = e.GetPosition(this);
                double pivotX = pt.X - dragBeginPoint.X;
                double pivotY = pt.Y - dragBeginPoint.Y;

                double leftEdge = canvasFrame.ActualWidth / 2 - imgFrame.Width / 2 - imgAnchor.Width / 2;
                double topEdge = (stackScene.ActualHeight - gridTimeline.ActualHeight) / 2 - imgFrame.Height / 2 - imgAnchor.Height / 2;

                double valueX = (dragBeginMargin.Left + pivotX - leftEdge) / imgFrame.Width;
                double valueY = (imgFrame.Height - (dragBeginMargin.Top + pivotY - topEdge)) / imgFrame.Height;
                valueX = Math.Round(valueX, 2);
                valueY = Math.Round(valueY, 2);
                valueX = Math.Min(Math.Max(valueX, 0), 1);
                valueY = Math.Min(Math.Max(valueY, 0), 1);
                sliderAnchorX.Value = anchorX = valueX;
                sliderAnchorY.Value = anchorY = valueY;
                txtAnchorX.Text = valueX + "";
                txtAnchorY.Text = valueY + "";
                UpdateAnchorImage();
            }
        }

        /**锚点松开*/
        private void grid_MouseUp(object sender, MouseButtonEventArgs e) {
            isDragingAnchor = false;
            Console.WriteLine("mouse up");

        }

        /**锚点松开*/
        private void canvasFrame_MouseLeave(object sender, MouseEventArgs e) {
            //isDragingAnchor = false;
            //Console.WriteLine("mouse leave");
        }
    }
}
