// Copyright 2020 The Oppia Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Unit tests for DisplayHintModalController.
 */

import { TestBed } from '@angular/core/testing';
import { InteractionObjectFactory } from
  'domain/exploration/InteractionObjectFactory';
import { RecordedVoiceoversObjectFactory } from
  'domain/exploration/RecordedVoiceoversObjectFactory';
import { StateCardObjectFactory } from
  'domain/state_card/StateCardObjectFactory';
import { SubtitledHtmlObjectFactory } from
  'domain/exploration/SubtitledHtmlObjectFactory';

describe('Display Hint Modal Controller', function() {
  var $rootScope = null;
  var $scope = null;
  var $uibModalInstance = null;
  var AudioPlayerService = null;
  var AutogeneratedAudioPlayerService = null;
  var AudioTranslationManagerService = null;
  var ContextService = null;
  var HintsAndSolutionManagerService = null;
  var interactionObjectFactory = null;
  var playerTranscriptService = null;
  var recordedVoiceoversObjectFactory = null;
  var stateCardObjectFactory = null;
  var subtitledHtmlObjectFactory = null;

  var card = null;
  var hintContent = null;

  beforeEach(angular.mock.module('oppia'));
  beforeEach(function() {
    interactionObjectFactory = TestBed.get(InteractionObjectFactory);
    recordedVoiceoversObjectFactory = TestBed.get(
      RecordedVoiceoversObjectFactory);
    stateCardObjectFactory = TestBed.get(StateCardObjectFactory);
    subtitledHtmlObjectFactory = TestBed.get(SubtitledHtmlObjectFactory);
  });

  beforeEach(angular.mock.inject(function($injector, $controller) {
    $rootScope = $injector.get('$rootScope');
    AudioPlayerService = $injector.get('AudioPlayerService');
    AutogeneratedAudioPlayerService = $injector.get(
      'AutogeneratedAudioPlayerService');
    AudioTranslationManagerService = $injector.get(
      'AudioTranslationManagerService');
    ContextService = $injector.get('ContextService');
    spyOn(ContextService, 'getExplorationId').and.returnValue('exp1');

    HintsAndSolutionManagerService = $injector.get(
      'HintsAndSolutionManagerService');
    playerTranscriptService = $injector.get('PlayerTranscriptService');

    $uibModalInstance = jasmine.createSpyObj(
      '$uibModalInstance', ['close', 'dismiss']);

    hintContent = subtitledHtmlObjectFactory.createDefault(
      'content_1', 'Hint Content');
    spyOn(HintsAndSolutionManagerService, 'displayHint').and.returnValue(
      hintContent);

    var interaction = interactionObjectFactory.createFromBackendDict({
      answer_groups: [],
      confirmed_unclassified_answers: [],
      customization_args: {},
      hints: [],
      id: 'interaction_1'
    });
    var recordedVoiceovers = recordedVoiceoversObjectFactory.createEmpty();
    card = stateCardObjectFactory.createNewCard(
      'Card 1', 'Content html', 'Interaction text', interaction,
      recordedVoiceovers, 'content_id');
    spyOn(playerTranscriptService, 'getCard').and.returnValue(card);

    spyOn($rootScope, '$broadcast').and.callThrough();

    $scope = $rootScope.$new();
    $controller('DisplayHintModalController', {
      $rootScope: $rootScope,
      $scope: $scope,
      $uibModalInstance: $uibModalInstance,
      index: 0
    });
  }));

  it('should evaluate initialized properties', function() {
    expect($scope.isHint).toBe(true);
    expect($scope.hint).toEqual(hintContent);

    expect($rootScope.$broadcast).toHaveBeenCalledWith('autoPlayAudio');
  });

  it('should dismiss modal', function() {
    spyOn(AudioPlayerService, 'stop');
    spyOn(AutogeneratedAudioPlayerService, 'cancel');
    spyOn(AudioTranslationManagerService, 'clearSecondaryAudioTranslations');
    $scope.closeModal();

    expect(AudioPlayerService.stop).toHaveBeenCalled();
    expect(AutogeneratedAudioPlayerService.cancel).toHaveBeenCalled();
    expect(AudioTranslationManagerService.clearSecondaryAudioTranslations)
      .toHaveBeenCalled();
    expect($uibModalInstance.dismiss).toHaveBeenCalledWith('cancel');
  });
});
