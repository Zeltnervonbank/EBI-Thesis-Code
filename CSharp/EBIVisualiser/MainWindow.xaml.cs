using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using OxyPlot;
using OxyPlot.Axes;
using OxyPlot.Series;
using OxyPlot.Wpf;
using HeatMapSeries = OxyPlot.Series.HeatMapSeries;
using LinearAxis = OxyPlot.Axes.LinearAxis;
using LinearColorAxis = OxyPlot.Axes.LinearColorAxis;
using LineSeries = OxyPlot.Series.LineSeries;
using ScatterSeries = OxyPlot.Series.ScatterSeries;

namespace EBIVisualiser
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow
    {
        private double[,] _heatmapData = new double[7, 7];
        private List<(double x, double y)> _scatterPositions = new List<(double x, double y)>();

        private List<string> _freqLabels = new List<string> {"1kHz", "2kHz", "3kHz", "7kHz", "11kHz", "17kHz", "23kHz", "31kHz", "43kHz", "61kHz", "89kHz", "127kHz", "179kHz", "251kHz", "349kHz" };
        public MainWindow()
        {
            InitializeComponent();

            PlotModel rawModel = new PlotModel {Title = "Raw Data"};
            RawPlot.Model = rawModel;

            PlotModel conductivityModel = new PlotModel {Title = "Conductivity Data"};
            conductivityModel.Axes.Add(new LinearAxis
            {
                Position = AxisPosition.Left,
            });
            ConductivityPlot.Model = conductivityModel;

            PlotModel predictionModel = new PlotModel {Title = "Prediction"};
            PredictionPlot.Model = predictionModel;


            var model = new PlotModel { Title = "Heatmap" };

            // Color axis (the X and Y axes are generated automatically)
            model.Axes.Add(new LinearColorAxis
            {
                Palette = OxyPalette.Interpolate(256, OxyColor.FromRgb(0, 0, 0), OxyColor.FromRgb(255, 255, 255))
            });
            
            PredictionPlot.Model = model;
            
            PlotModel positionModel = new PlotModel {Title = "Active Search Positions"};

            PositionPlot.Model = positionModel;
            
            Task t = new Task(TcpConnection);
            t.Start();
        }

        private void AddHeatPoint(int x, int y, double val)
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                PredictionPlot.Model.Series.Clear();
                _heatmapData[x, y] = val;
                var heatMapSeries = new HeatMapSeries
                {
                    X0 = -20,
                    X1 = 20,
                    Y0 = -20,
                    Y1 = 20,
                    Interpolate = false,
                    RenderMethod = HeatMapRenderMethod.Bitmap,
                    Data = _heatmapData
                };

                PredictionPlot.Model.Series.Add(heatMapSeries);

                PredictionPlot.InvalidatePlot(true);
            });
        }

        private void AddScatterPoint(double x, double y)
        {
            _scatterPositions.Add((x, y));
            Application.Current.Dispatcher.Invoke(() =>
            {
                PositionPlot.Model.Series.Clear();
                var scatterSeries = new ScatterSeries
                {
                    MarkerType = MarkerType.Circle
                };

                foreach ((double x, double y) point in _scatterPositions)
                {
                    scatterSeries.Points.Add(new ScatterPoint(point.x, point.y, 5));
                }
                PositionPlot.Model.Series.Add(scatterSeries);

                PositionPlot.InvalidatePlot();
            });
        }

        private void AddMultipleDataRanges(List<LineSeries> seriesList, PlotView view)
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                foreach (LineSeries series in seriesList)
                {
                    view.Model.Series.Add(series);
                }
                view.InvalidatePlot();
            });
        }
        private void ClearPlot(PlotView view)
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                view.Model.Series.Clear();
                view.InvalidatePlot();
            });
        }

        private List<LineSeries> ConvertToSeries(Dictionary<int, List<double>> dataSeries)
        {
            List<LineSeries> series = new List<LineSeries>();

            foreach (KeyValuePair<int, List<double>> freqData in dataSeries)
            {
                LineSeries s = new LineSeries { Title = $"{_freqLabels[freqData.Key]}" };
                int x = 0;
                s.Points.AddRange(freqData.Value.Select(p => new DataPoint(x++, p)));
                series.Add(s);
            }

            return series;
        }
        
        private (Dictionary<int, List<double>>, List<List<double>>) SeparateValues(string data)
        {
            if (data.Contains('C'))
            {
                data = data.Remove(data.LastIndexOf('C'));
            }
            string cleanData = data.Replace("[", "").Replace("]", "");
            string[] split = cleanData.Split("|");
            Dictionary<int, List<double>> dataSeries = new Dictionary<int, List<double>>();
            List<List<double>> freqSorted = new List<List<double>>();
            foreach (string val in split)
            {
                string[] strVals = val.Split(";");
                if (strVals.All(p => p.Contains(')')))
                {
                    strVals = strVals.Select(p => p.Remove(p.LastIndexOf(',')).Replace("(", "")).ToArray();
                }

                List<double> seriesVals = strVals.Select(Convert.ToDouble).ToList();
                freqSorted.Add(seriesVals);
                for (int freq = 0; freq < seriesVals.Count; freq++)
                {
                    if (!dataSeries.ContainsKey(freq))
                    {
                        dataSeries.Add(freq, new List<double>());
                    }
                    dataSeries[freq].Add(seriesVals[freq]);
                }
            }

            return (dataSeries, freqSorted);
        }

        private void TcpConnection()
        {
            TcpListener server = null;
            try
            {
                int port = 5005;
                IPAddress localAddr = IPAddress.Parse("127.0.0.1");

                server = new TcpListener(localAddr, port);

                // Start listening for client requests.
                server.Start();

                // Buffer for reading data
                byte[] bytes = new byte[10000];

                // Enter the listening loop.
                while (true)
                {
                    // Perform a blocking call to accept requests.
                    TcpClient client = server.AcceptTcpClient();

                    // Get a stream object for reading and writing
                    NetworkStream stream = client.GetStream();

                    int i;

                    // Loop to receive all the data sent by the client.
                    while ((i = stream.Read(bytes, 0, bytes.Length)) != 0)
                    {
                        try
                        {

                            // Translate data bytes to a ASCII string.
                            string data = Encoding.UTF8.GetString(bytes, 0, i);

                            switch (data[0])
                            {
                                case 'C':
                                {
                                    ClearPlot(ConductivityPlot);
                                    string conductivityData = data.Remove(0, 1);
                                    (Dictionary<int, List<double>> dataSeries, List<List<double>> freqSorted) = SeparateValues(conductivityData);
                                    AddMultipleDataRanges(ConvertToSeries(dataSeries), ConductivityPlot);
                                    break;
                                }
                                case 'R':
                                {
                                    ClearPlot(RawPlot);
                                    string rawData = data.Remove(0, 1);
                                    (Dictionary<int, List<double>> dataSeries, List<List<double>> freqSorted) = SeparateValues(rawData);
                                    AddMultipleDataRanges(ConvertToSeries(dataSeries), RawPlot);
                                    break;
                                }
                                case 'P':
                                {
                                    string rawData = data.Remove(0, 1);
                                    string cleanData = rawData.Replace("[", "").Replace("]", "");
                                    string[] split = cleanData.Split(";");
                                    int x = Convert.ToInt32(split[0]);
                                    int y = Convert.ToInt32(split[1]);
                                    double z = Convert.ToDouble(split[2]);
                                    AddHeatPoint(x, y, z);
                                    break;
                                }
                                case 'A':
                                {
                                    string rawData = data.Remove(0, 1);
                                    string cleanData = rawData.Replace("[", "").Replace("]", "");
                                    string[] split = cleanData.Split(";");
                                    double x = Convert.ToDouble(split[0]);
                                    double y = Convert.ToDouble(split[1]);
                                    AddScatterPoint(x, y);
                                    break;
                                }
                            }
                        }
                        catch (Exception)
                        {
                        }
                    }
                }
            }
            catch (SocketException e)
            {
                Console.WriteLine("SocketException: {0}", e);
            }
            finally
            {
                // Stop listening for new clients.
                server?.Stop();
            }
        }
    }
}
