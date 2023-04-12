/**
 * Copyright (c) 2019-2021 LG Electronics, Inc.
 *
 * This software contains code licensed as described in LICENSE.
 *
 */

using System.Collections;
using System.Collections.Generic;
using System.Text;
using System.IO;
using System.Reflection;
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
using UnityEngine.AI;


public class NPCItineraryBehaviour : NPCLaneFollowBehaviour
{
    public List<MapTrafficLane> itinerary = new List<MapTrafficLane>();
    public int itineraryIndex = 0;

    public float itineraryEndOffset;

    public MapTrafficLane drivingLane;
    public float drivingOffset;
    public float drivingSpeed;
    public float drivingAcceleration;
    public float controlAcceleration;
    public bool atStopTargetP = false;
    public bool reachedDestination = false;
    private float prevDrivingSpeed;
    private float prevSpeed;
    public Vector3 itineraryStopTarget = new Vector3(0, 0, 0);

    public List<State> stateRecord = new List<State>();

    #region mono
    public override void PhysicsUpdate()
    {
        if (isLaneDataSet)
        {
            ToggleBrakeLights(); // move to set target speed and call controller?
            CollisionCheck();
            EvaluateTarget();
            UpdateItinerary(); // new for FollowItinerary
            GetDodge();
            SetTargetSpeed();
            SetTargetTurn();
            NPCTurn();
            NPCMove();
            StopTimeDespawnCheck();
            EvaluateDistanceFromFocus();
            recordState();
        }
    }
    #endregion

    public class State {
        public string laneId;
        public float laneOffset;
        public float longitudinalSpeed;
        public float controlSpeed;
        public float longitudinalAcceleration;
        public float controlAcceleration;
        public int itineraryIndex;
        public float targetSpeed;
        public bool atStopTarget;
        public bool reachedDestination;
        public float turn;
        public float targetTurn;
        public Vector3 position;
        public Vector3 velocity;
    }

    protected void recordState() {
        stateRecord.Add(new State{
            laneId = drivingLane.id,
            laneOffset = drivingOffset,
            longitudinalSpeed = drivingSpeed,
            controlSpeed = currentSpeed,
            longitudinalAcceleration = drivingAcceleration,
            controlAcceleration = controlAcceleration,
            itineraryIndex = itineraryIndex,
            targetSpeed = targetSpeed,
            atStopTarget = atStopTargetP,
            reachedDestination = reachedDestination,
            turn = currentTurn,
            targetTurn = targetTurn,
            position = transform.position,
            velocity = controller.GetVelocity()
        });
    }

    protected void ReachDestination() {
        if (reachedDestination == false) {
            ApiManager.Instance.AddDestinationReached(gameObject);
        }
        reachedDestination = true;
    }

    protected bool HasStopped() {
        return Mathf.Abs(currentSpeed) < 1e-6;
    }

    protected void UpdateItinerary() {
        if (drivingLane.id != currentMapLane.id) {
            // Correct currentMapLane;
            if (itineraryIndex < itinerary.Count - 1 && currentMapLane != itinerary[itineraryIndex + 1]) {
                currentMapLane = itinerary[itineraryIndex + 1];
                
                laneSpeedLimit = currentMapLane.speedLimit;
                aggressionAdjustRate = laneSpeedLimit / 11.176f; // 11.176 m/s corresponds to 25 mph
                normalSpeed =  laneSpeedLimit;
                // APIMaxSpeed > 0 ?
                //     Mathf.Min(APIMaxSpeed, laneSpeedLimit) :
                //     RandomGenerator.NextFloat(laneSpeedLimit, laneSpeedLimit + 1 + aggression); // API set max speed or lane speed limit
                SetLaneData(currentMapLane.mapWorldPositions);
                SetTurnSignal();

                var path = transform.InverseTransformPoint(currentTarget).x;
                isCurve = path < -1f || path > 1f ? true : false;
            }

            // Update driving lane
            var crossPosition = drivingLane.mapWorldPositions[drivingLane.mapLocalPositions.Count-1];
            crossPosition = new Vector3(crossPosition.x, 0f, crossPosition.z);
            var forward = new Vector3(controller.frontCenter.forward.x, 0f, controller.frontCenter.forward.z);
            var position = new Vector3(controller.frontCenter.position.x, 0f, controller.frontCenter.position.z);
            var gap = (crossPosition - position);
            if (Vector3.Dot(forward, gap.normalized) < 0)
            { 
                drivingLane = currentMapLane;
                if (itineraryIndex < itinerary.Count - 1) {
                    itineraryIndex++;
                }
            }
        }
        
        updateDrivingState();

        if (itineraryIndex == itinerary.Count - 1) {
            // Set stop target
            stopTarget = itineraryStopTarget;
            if (0 < distanceToStopTarget && distanceToStopTarget < stopLineDistance) {
                isStopSign = true;
                if (distanceToStopTarget < minTargetDistance) {
                    hasReachedStopSign = true;
                    if (HasStopped()) {
                        ReachDestination();
                    }
                }
            }
            if (!reachedDestination && frontClosestHitInfo.collider) {
                var frontNpc = frontClosestHitInfo.collider.GetComponentInParent<NPCItineraryBehaviour>();
                if (frontNpc && frontNpc.reachedDestination && HasStopped()) {
                    ReachDestination();
                }
            }
        }
    }

    private void updateDrivingState() {
        prevDrivingSpeed = drivingSpeed;
        drivingOffset = 0;
        drivingSpeed = 0;
        int index = -1;
        float minDist = float.PositiveInfinity;
        Vector3 closest = Vector3.zero;
        var position = controller.frontCenter.position;
        position = new Vector3(position.x, 0f, position.z);
        for (int i = 0; i < drivingLane.mapWorldPositions.Count - 1; i++) {
            var p0 = drivingLane.mapWorldPositions[i];
            p0 = new Vector3(p0.x, 0f, p0.z);
            var p1 = drivingLane.mapWorldPositions[i + 1];
            p1 = new Vector3(p1.x, 0f, p1.z);

            var p = Utility.ClosetPointOnSegment(p0, p1, position);

            float d = Vector3.SqrMagnitude(position - p);
            if (d < minDist)
            {
                minDist = d;
                index = i;
                closest = p;
            }
        }
        for (int i = 0; i < drivingLane.mapWorldPositions.Count - 1; i++) {
            var p0 = drivingLane.mapWorldPositions[i];
            p0 = new Vector3(p0.x, 0f, p0.z);
            var p1 = drivingLane.mapWorldPositions[i + 1];
            p1 = new Vector3(p1.x, 0f, p1.z);
            if (i == index) {
                drivingOffset = drivingOffset + Vector3.Magnitude(closest - p0);
                var vel = controller.GetVelocity();
                vel = new Vector3(vel.x, 0f, vel.z);
                drivingSpeed = Vector3.Dot(Vector3.Normalize(p1 - p0), vel);
                break;
            }
            drivingOffset += Vector3.Magnitude(p1 - p0);
        }

        drivingAcceleration = (drivingSpeed - prevDrivingSpeed) / Time.fixedDeltaTime;
        controlAcceleration = (currentSpeed - prevSpeed) / Time.fixedDeltaTime;
        atStopTargetP = atStopTarget;
        prevSpeed = currentSpeed;
        
    }

    public void SetItinerary(List<string> laneIds, float endOffset, float initialSpeed) {
        itinerary.Clear();
        foreach (var laneId in laneIds) {
            itinerary.Add(ExternalMapManager.Instance.mapLanes[laneId]);
        }
        itineraryEndOffset = endOffset;
        itineraryIndex = 0;
        drivingLane = itinerary[itineraryIndex];
        var currentLane = SimulatorManager.Instance.MapManager.GetClosestLane(transform.position);
        if (currentLane.id != drivingLane.id) {
            throw new ArgumentException("The position of the vehicle is not on the itinerary");
        }
        itineraryStopTarget = ExternalMapManager.GetLanePoint(itinerary[itinerary.Count - 1], endOffset);
        APIMaxSpeed = drivingLane.speedLimit;
        SetFollowClosestLane(drivingLane.speedLimit, false);
        normalSpeed = drivingLane.speedLimit;
        reachedDestination = false;
        EvaluateTarget();
        UpdateItinerary();
        recordState();
        // turnAdjustRate = 10f;
        prevSpeed = prevDrivingSpeed = drivingSpeed = currentSpeed = initialSpeed;
        if (distanceToStopTarget < minTargetDistance) {
            atStopTargetP = true;
        }
        else {
            atStopTargetP = false;
        }
    }

    // protected virtual void SetTargetTurn()
    // {
    //     var ct = new Vector3(currentTarget.x, 0f, currentTarget.z);
    //     var fc = new Vector3(controller.frontCenter.position.x, 0f, controller.frontCenter.position.z);
    //     var ff = new Vector3(controller.frontCenter.forward.x, 0f, controller.frontCenter.forward.z);
    //     controller.steerVector = (ct - fc).normalized;

    //     float steer = Vector3.Angle(controller.steerVector, ff) * 1.5f;
    //     targetTurn = Vector3.Cross(ff, controller.steerVector).y < 0 ? -steer : steer;
    //     currentTurn += turnAdjustRate * Time.fixedDeltaTime * (targetTurn - currentTurn);

    //     if (targetSpeed == 0)
    //     {
    //         currentTurn = 0;
    //     }
    // }
}


class VehicleFollowItinerary : ICommand
{
    public string Name => "vehicle/follow_itinerary";

    private bool CheckItinerary(List<string> laneIds, double endOffset) {
        var mapLanes = ExternalMapManager.Instance.mapLanes;
        if (ExternalMapManager.GetLaneLength(mapLanes[laneIds[laneIds.Count-1]]) < endOffset || endOffset < 0) {
            Debug.LogWarning($"The endoffset {endOffset} is given, which is not within the lenght of {mapLanes[laneIds[laneIds.Count-1]]} ({ExternalMapManager.GetLaneLength(mapLanes[laneIds[laneIds.Count-1]])})");
            return false;
        }
        for (int i = 0; i < laneIds.Count - 1; i++) {
            var currentLane = mapLanes[laneIds[i]];
            bool isConnected = false;
            foreach (var nextLane in currentLane.nextConnectedLanes) {
                if (nextLane.id.Equals(laneIds[i + 1])) {
                    isConnected = true;
                    break;
                }
            }
            if (!isConnected) {
                Debug.LogWarning($"{currentLane.id} is not connected with {laneIds[i+1]}");
                return false;
            }
        }
        return true;
    }

    public void Execute(JSONNode args)
    {
        var uid = args["uid"].Value;
        var follow = args["follow"].AsBool;
        var api = ApiManager.Instance;

        if (api.Agents.TryGetValue(uid, out GameObject obj))
        {
            var npc = obj.GetComponent<NPCController>();
            if (npc == null)
            {
                api.SendError(this, $"Agent '{uid}' is not a NPC agent");
                return;
            }

            if (follow)
            {
                var itineraryJson = args["itinerary"].AsArray;
                var endOffset = args["end_offset"].AsFloat;
                var initialSpeed = args["initial_speed"].AsFloat;
                var itinerary = new List<string>();
                for (var i = 0; i < itineraryJson.Count; i++) {
                    itinerary.Add(itineraryJson[i]);
                }
                if (!CheckItinerary(itinerary, endOffset)) {
                    api.SendError(this, $"The given itinerary is not connected");
                    return;
                }
                var laneFollow = npc.SetBehaviour<NPCItineraryBehaviour>();
                laneFollow.SetItinerary(itinerary, endOffset, initialSpeed);
            }
            else
            {
                npc.SetBehaviour<NPCManualBehaviour>();
            }
            api.SendResult(this);
        }
        else
        {
            api.SendError(this, $"Agent '{uid}' not found");
        }
    }
}


class VehicleGetLane : ICommand
    {
        public string Name => "vehicle/get_state";

        public void Execute(JSONNode args)
        {
            var uid = args["uid"].Value;
            var api = ApiManager.Instance;

            if (api.Agents.TryGetValue(uid, out GameObject obj))
            {
                var npc = obj.GetComponent<NPCItineraryBehaviour>();
                if (npc == null)
                {
                    api.SendError(this, $"Agent '{uid}' is not a NPC agent with lane capabilities");
                    return;
                }

                var result = new JSONObject();
                string lane_id;
                if (string.IsNullOrEmpty(npc.drivingLane.id))
                {
                    lane_id = "null";
                }
                else {
                    lane_id = npc.drivingLane.id;
                }
                result.Add("lane_id", lane_id);
                result.Add("lane_offset", npc.drivingOffset);
                result.Add("longitudinal_speed", npc.drivingSpeed);
                result.Add("control_speed", npc.currentSpeed);
                result.Add("longitudinal_acceleration", npc.drivingAcceleration);
                result.Add("control_acceleration", npc.controlAcceleration);
                result.Add("itinerary_index", npc.itineraryIndex);
                result.Add("target_speed", npc.targetSpeed);
                result.Add("at_stop_target", npc.atStopTargetP);
                result.Add("reached_destination", npc.reachedDestination);
                result.Add("turn", npc.currentTurn);
                result.Add("target_turn", npc.targetTurn);
                api.SendResult(this, result);
            }
            else
            {
                api.SendError(this, $"Agent '{uid}' not found");
            }
        }
    }

class VehicleGetAggression : ICommand
{
    public string Name => "vehicle/get_aggression";

    public void Execute(JSONNode args)
    {
        var uid = args["uid"].Value;
        var api = ApiManager.Instance;

        if (api.Agents.TryGetValue(uid, out GameObject obj))
            {
                var npc = obj.GetComponent<NPCLaneFollowBehaviour>();
                if (npc == null)
                {
                    api.SendError(this, $"Agent '{uid}' is not a NPC agent with lane capabilities");
                    return;
                }
                api.SendResult(this, npc.aggression);
            }
            else
            {
                api.SendError(this, $"Agent '{uid}' not found");
            }

    }
}

class VehicleGetStateSeq : ICommand
    {
        public string Name => "vehicle/get_state_record";

        public void Execute(JSONNode args)
        {
            var uid = args["uid"].Value;
            var api = ApiManager.Instance;

            if (api.Agents.TryGetValue(uid, out GameObject obj))
            {
                var npc = obj.GetComponent<NPCItineraryBehaviour>();
                if (npc == null)
                {
                    api.SendError(this, $"Agent '{uid}' is not a NPC agent with lane capabilities");
                    return;
                }

                var result = new JSONArray();
                foreach(var state in npc.stateRecord) {
                    var item = new JSONObject();
                    item.Add("lane_id", state.laneId);
                    item.Add("lane_offset", state.laneOffset);
                    item.Add("longitudinal_speed", state.longitudinalSpeed);
                    item.Add("control_speed", state.controlSpeed);
                    item.Add("longitudinal_acceleration", state.longitudinalAcceleration);
                    item.Add("control_acceleration", state.controlAcceleration);
                    item.Add("itinerary_index", state.itineraryIndex);
                    item.Add("target_speed", state.targetSpeed);
                    item.Add("at_stop_target", state.atStopTarget);
                    item.Add("reached_destination", state.reachedDestination);
                    item.Add("turn", state.turn);
                    item.Add("target_turn", state.targetTurn);
                    var physicalState = new JSONObject();
                    physicalState.Add("position", state.position);
                    physicalState.Add("velocity", state.velocity);
                    item.Add("physical_state", physicalState);
                    result.Add(item);
                }
                api.SendResult(this, result);
            }
            else
            {
                api.SendError(this, $"Agent '{uid}' not found");
            }
        }
    }


class VehicleGetHalfLength : ICommand
    {
        public string Name => "vehicle/half_length/get";

        public void Execute(JSONNode args)
        {
            var uid = args["uid"].Value;
            var api = ApiManager.Instance;
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
                float ret = (front - center).magnitude;

                api.SendResult(this, ret);
            }
            else
            {
                api.SendError(this, $"Agent '{uid}' not found");
            }
            
        }
    }
    