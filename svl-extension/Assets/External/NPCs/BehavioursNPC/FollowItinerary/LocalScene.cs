using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.IO;
using System;
using UnityEngine;
using UnityEngine.SceneManagement;
using SimpleJSON;
using ICSharpCode.SharpZipLib.Zip;
using VirtualFileSystem;
using System.Threading.Tasks;
using Simulator.Web;
using Simulator.Api;
using Simulator.Map;
using Simulator.Utilities;


public class SignalRecorderClass {
    private Dictionary<string, MapSignal> signals = new Dictionary<string, MapSignal>();
    public Dictionary<string, List<string>> record = new Dictionary<string, List<string>>();
    public HashSet<Coroutine> Coroutines = new HashSet<Coroutine>();

    public void Reset() {
        signals.Clear();
        record.Clear();
    }

    public void Clear() {
        foreach (var item in record) {
            item.Value.Clear();
        }
    }

    public void Init(List<string> UIDList) {
        Reset();
        var MapAnnotationData = new MapManagerData();
        foreach (MapSignal signal in MapAnnotationData.GetData<MapSignal>()) {
            if (UIDList.Contains(signal.UID)) {
                signals[signal.UID] = signal;
                record[signal.UID] = new List<string>();
            }
        }
    }

    public void StartRecord() {
        var fixedUpdateManager = SimulatorManager.Instance.FixedUpdateManager;
        Coroutines.Add(fixedUpdateManager.StartCoroutine(Record()));
    }

    private IEnumerator Record()
    {
        // int frame = SimulatorManager.Instance.CurrentFrame;
        while (true) {
            foreach (var item in signals) {
                record[item.Key].Add(item.Value.CurrentState);
            }
            yield return new WaitForFixedUpdate();
        }
    }
}


public class ExternalMapManager
    {

        public SignalRecorderClass SignalRecorder = new SignalRecorderClass();

        public static double GetSqrClosestDistance(MapTrafficLane lane, Vector3 position) {
            var p0 = lane.mapWorldPositions[0];
            var p1 = lane.mapWorldPositions[1];
            double minSqrDistance = Utility.SqrDistanceToSegment(p0, p1, position);
            for (int i = 2; i < lane.mapLocalPositions.Count; i++) {
                p0 = p1;
                p1 = lane.mapLocalPositions[i];
                double sqrDistance = Utility.SqrDistanceToSegment(p0, p1, position);
                if (sqrDistance < minSqrDistance) {
                    minSqrDistance = sqrDistance;
                }
            }
            return minSqrDistance;
        }

        public static float GetLaneLength(MapTrafficLane lane) {
            float length;
            length = 0f;
            for (int i = 0; i < lane.mapWorldPositions.Count-1; i++) {
                var p1 = lane.mapWorldPositions[i];
                var p2 = lane.mapWorldPositions[i + 1];
                length += Vector3.Distance(p1, p2);
            }
            return length;
        }

        public static Vector3 GetLanePoint(MapTrafficLane lane, float offset) {
            if (offset < 0)
                throw new ArgumentOutOfRangeException($"The given offset should not be negative ({offset} was given)");
            Vector3 prevPoint = lane.mapWorldPositions[0];
            for (int i = 1; i < lane.mapWorldPositions.Count; i++) {
                var curPoint = lane.mapWorldPositions[i];
                var length = Vector3.Magnitude(curPoint - prevPoint);
                if (length >= offset) {
                    var direction = curPoint - prevPoint;
                    float rate = offset / length;
                    direction = new Vector3(direction.x * rate, direction.y * rate, direction.z * rate);
                    return prevPoint + direction;
                }
                offset -= length;
                prevPoint = curPoint;
            }
            throw new ArgumentOutOfRangeException($"The given offset shloud not greater than the length of lane ({offset} was given, but the length is {ExternalMapManager.GetLaneLength(lane)})");
        }

        private static ExternalMapManager _instance = new ExternalMapManager();
        public static ExternalMapManager Instance 
        {
            get 
            {
                if (_instance == null) 
                {
                    _instance = new ExternalMapManager();
                }
                return _instance;
            }
        }
        private ExternalMapManager() {}
        private bool _isDataLoaded = false;
        private Dictionary<string, MapTrafficLane> _mapLanes = new Dictionary<string, MapTrafficLane>();
        public Dictionary<string, MapTrafficLane> mapLanes
        {
            get
            {
                if (!_isDataLoaded) {
                    LoadData();
                    if (!_isDataLoaded) {
                        Debug.LogWarning("Map data cannot be loaded");
                        return null;
                    }
                }
                return _mapLanes;
            }
        }

        public void LoadData() 
        {
            if (SimulatorManager.Instance == null) {
                Debug.LogWarning("simlator manager is null");
            }
            var mapManager = SimulatorManager.Instance.MapManager;
            int idCnt = 0;
            foreach (var lane in mapManager.allLanes) {
                string laneId = $"lane_{idCnt}";
                _mapLanes[laneId] = lane;
                lane.id = laneId;
                idCnt++;
            }
            _isDataLoaded = true;
        }

        public void ClearData() 
        {
            _isDataLoaded = false;
            _mapLanes.Clear();
            SignalRecorder.Reset();
        }

    }


namespace Simulator.Api.Commands
{
    class LoadLocalScene : IDistributedCommand, ILockingCommand
    {
        public string Name => "simulator/load_local_scene";

        public string LockingGuid { get; set; }

        public float StartRealtime { get; set; }

        public event Action<ILockingCommand> Executed;

        private async Task LoadMap(JSONNode args, string userMapId, int? seed = null)
        {
            var api = ApiManager.Instance;
            api.StartCoroutine(LoadMapAssets(this, $"AssetBundles/Environments/environment_{userMapId}", userMapId, seed));
        }

        static IEnumerator LoadMapAssets(LoadLocalScene sourceCommand, string localPath, string userMapId, int? seed = null)
        {
            var api = ApiManager.Instance;

            AssetBundle textureBundle = null;
            AssetBundle mapBundle = null;

            ZipFile zip = new ZipFile(localPath);
            MapDetailData map = new MapDetailData();
            try
            {
                Manifest manifest;
                ZipEntry entry = zip.GetEntry("manifest.json");
                using (var ms = zip.GetInputStream(entry))
                {
                    int streamSize = (int)entry.Size;
                    byte[] buffer = new byte[streamSize];
                    streamSize = ms.Read(buffer, 0, streamSize);
                    manifest = Newtonsoft.Json.JsonConvert.DeserializeObject<Manifest>(Encoding.UTF8.GetString(buffer));
                }

                if (manifest.assetFormat != BundleConfig.Versions[BundleConfig.BundleTypes.Environment])
                {
                    zip.Close();
                    api.SendError(sourceCommand,
                        "Out of date Map AssetBundle. Please check content website for updated bundle or rebuild the bundle.");
                    sourceCommand.Executed?.Invoke(sourceCommand);
                    yield break;
                }

                if (zip.FindEntry($"{manifest.assetGuid}_environment_textures", true) != -1)
                {
                    entry = zip.GetEntry($"{manifest.assetGuid}_environment_textures");
                    var texStream = ExternalVirtualFileSystem.VirtualFileSystem.EnsureSeekable(zip.GetInputStream(entry), entry.Size);
                    textureBundle = AssetBundle.LoadFromStream(texStream, 0, 1 << 20);
                    texStream.Close();
                    texStream.Dispose();
                }

                string platform = SystemInfo.operatingSystemFamily == OperatingSystemFamily.Windows
                    ? "windows"
                    : "linux";
                var mapStream =
                    zip.GetInputStream(zip.GetEntry($"{manifest.assetGuid}_environment_main_{platform}"));
                mapBundle = AssetBundle.LoadFromStream(mapStream, 0, 1 << 20);

                if (mapBundle == null)
                {
                    api.SendError(sourceCommand, $"Failed to load environment from '{map.AssetGuid}' asset bundle '{map.Name}'");
                    sourceCommand.Executed?.Invoke(sourceCommand);
                    yield break;
                }

                textureBundle?.LoadAllAssets();

                var scenes = mapBundle.GetAllScenePaths();
                if (scenes.Length != 1)
                {
                    api.SendError(sourceCommand, $"Unsupported environment in '{map.AssetGuid}' asset bundle '{map.Name}', only 1 scene expected");
                    sourceCommand.Executed?.Invoke(sourceCommand);
                    yield break;
                }

                var sceneName = Path.GetFileNameWithoutExtension(scenes[0]);

                var loader = SceneManager.LoadSceneAsync(sceneName, LoadSceneMode.Single);
                yield return new WaitUntil(() => loader.isDone);

                if (Loader.Instance.SimConfig != null)
                {
                    Loader.Instance.SimConfig.Seed = seed;
                    Loader.Instance.SimConfig.MapName = map.Name;
                    Loader.Instance.SimConfig.MapAssetGuid = map.AssetGuid;
                }

                var sim = Loader.Instance.CreateSimulatorManager();
                sim.Init(seed);

                if (Loader.Instance.CurrentSimulation != null)
                {
                    Loader.Instance.reportStatus(SimulatorStatus.Running);
                }

            }
            finally
            {
                textureBundle?.Unload(false);
                mapBundle?.Unload(false);
                zip.Close();
            }

            var resetTask = api.Reset();
            while (!resetTask.IsCompleted)
                yield return null;
            api.CurrentSceneId = userMapId;
            api.CurrentSceneName = map.Name;
            api.CurrentScene = userMapId;
            sourceCommand.Executed?.Invoke(sourceCommand);
            api.SendResult(sourceCommand);
        }

        public async void Execute(JSONNode args)
        {
            var api = ApiManager.Instance;
            var mapId = args["scene"].Value;
            int? seed = null;
            if (!args["seed"].IsNull)
            {
                seed = args["seed"].AsInt;
            }
            try
            {
                await LoadMap(args, mapId, seed);
                ExternalMapManager.Instance.ClearData();
            }
            catch (Exception e)
            {
                api.SendError(this, e.Message);
                // only unlock in error case as map loading continues in coroutine after which we unlock
                Executed?.Invoke(this);
            }
        }
    }

    class GetLanePositions : ICommand
    {
        public string Name => "map/get_lanes";

        public void Execute(JSONNode args)
        {
            var api = ApiManager.Instance;
            
            var result = new JSONObject();
            foreach (var lane in ExternalMapManager.Instance.mapLanes) {
                var curResult = new JSONObject();
                var positions = new JSONArray();
                for (var i = 0; i < lane.Value.mapWorldPositions.Count; i++) {
                    var position = lane.Value.mapWorldPositions[i];
                    var jsonPosition = new JSONObject();
                    jsonPosition.Add("x", position.z);
                    jsonPosition.Add("y", -position.x);
                    positions.Add(jsonPosition);
                }
                curResult.Add("positions", positions);
                curResult.Add("length", ExternalMapManager.GetLaneLength(lane.Value));
                result.Add(lane.Key, curResult);
            }
            api.SendResult(this, result);
        }
    }

    class LocalReset : IDistributedCommand
    {
        public string Name => "simulator/local_reset";

        private static async Task ResetAsync(LocalReset sourceCommand)
        {
            var api = ApiManager.Instance;
            await api.Reset();
            ApiManager.Instance.SendResult(sourceCommand);
            ExternalMapManager.Instance.SignalRecorder.Clear();
        }

        public void Execute(JSONNode args)
        {
            var nonBlockingTask = ResetAsync(this);
        }
    }


    class StartSignalRecord : ICommand
    {
        public string Name => "signals/start_record";

        public void Execute(JSONNode args) {
            var signalsJSON = args["signals"].AsArray;
            var api = ApiManager.Instance;

            var signals = new List<string>();
            for (var i = 0; i < signalsJSON.Count; i++) {
                signals.Add(signalsJSON[i]);
            }
            ExternalMapManager.Instance.SignalRecorder.Init(signals);
            ExternalMapManager.Instance.SignalRecorder.StartRecord();
            
            api.SendResult(this);
        }
    }

    class GetSignalRecord : ICommand
    {
        public string Name => "signals/get_record";

        public void Execute(JSONNode args) {
            var api = ApiManager.Instance;

            var result = new JSONObject();

            foreach (var item in ExternalMapManager.Instance.SignalRecorder.record) {
                var seq = new JSONArray();
                foreach (string color in item.Value) {
                    seq.Add(color);
                }
                result.Add(item.Key, seq);
            }

            api.SendResult(this, result);
        }
    }

    class ResetSignalRecord : ICommand
    {
        public string Name => "signals/reset_record";

        public void Execute(JSONNode args) {
            var api = ApiManager.Instance;
            ExternalMapManager.Instance.SignalRecorder.Reset();
            api.SendResult(this);
        }
    }

    class ClearSignalRecord : ICommand
    {
        public string Name => "signals/clear_record";

        public void Execute(JSONNode args) {
            var api = ApiManager.Instance;
            ExternalMapManager.Instance.SignalRecorder.Clear();
            api.SendResult(this);
        }
    }

    class SetLaneState : ICommand
    {
        public string Name => "vehicle/lane_state/set";

        public void Execute(JSONNode args)
        {
            var api = ApiManager.Instance;
            
            var uid = args["uid"].Value;
            var laneId = args["lane_id"].Value;
            var offset = args["offset"].AsFloat;

            if (api.Agents.TryGetValue(uid, out GameObject obj))
            {
                var controller = obj.GetComponent<NPCController>();
                if (controller == null)
                {
                    api.SendError(this, $"Agent '{uid}' is not a NPC agent with controller");
                    return;
                }

                
                var front = new Vector3(controller.frontCenter.position.x, 0f, controller.frontCenter.position.z);
                var center = new Vector3(obj.transform.position.x, 0f, obj.transform.position.z);
                float halfLength = Vector3.Distance(front, center);

                
                var lane = ExternalMapManager.Instance.mapLanes[laneId];
                float laneLength = ExternalMapManager.GetLaneLength(lane);
                if (offset < 0 || offset > laneLength) {
                    api.SendError(this, $"offset is out of range [0, {laneLength}]. {offset} is given");
                    return;
                }

                var targetPoint = Vector3.zero;
                var targetP0 = Vector3.zero;
                var targetP1 = Vector3.zero;
                for (int i = 0; i < lane.mapWorldPositions.Count - 1; i++) {
                    var p0 = lane.mapWorldPositions[i];
                    var p1 = lane.mapWorldPositions[i + 1];
                    float distance = Vector3.Distance(p0, p1);
                    if (offset <= distance) {
                        targetPoint = p0 + (p1 - p0).normalized * offset;
                        targetP0 = p0;
                        targetP1 = p1;
                        break;
                    }
                    offset -= distance;
                }

                Vector3 position;
                Quaternion rotation;
                SimulatorManager.Instance.MapManager.GetPointOnLane(targetPoint, out position, out rotation);

                var centerPosition = position + (targetP0 - targetP1).normalized * halfLength;
                obj.transform.SetPositionAndRotation(centerPosition, rotation);

                api.SendResult(this);
            }
            else
            {
                api.SendError(this, $"Agent '{uid}' not found");
            }
        }
    }

}
