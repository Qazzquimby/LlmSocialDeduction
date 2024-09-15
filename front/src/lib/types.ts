/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface BaseEvent {
  type: string;
}
export interface BaseMessage {
  type: string;
  message: string;
  username?: string;
}
export interface GameConnectMessage {
  type?: "game_connect";
  message: string;
  username?: string;
  gameId: string;
}
export interface GameStartedMessage {
  type?: "game_started";
  message: string;
  username?: string;
  players: string[];
}
export interface NextSpeakerMessage {
  type?: "next_speaker";
  player: string;
}
export interface ObservationMessage {
  type?: "observation";
  message: string;
  username?: string;
}
export interface PhaseMessage {
  type?: "phase";
  phase: string;
}
export interface PlayerActionMessage {
  type?: "player_action";
  message?: string | null;
  username?: string;
  player: string;
  action: string;
}
export interface PromptMessage {
  type?: "prompt";
  message: string;
  username?: string;
}
export interface RulesError {
  type?: "rules_error";
  message: string;
  username?: string;
}
export interface SpeechMessage {
  type?: "speech";
  message: string;
  username?: string;
}
