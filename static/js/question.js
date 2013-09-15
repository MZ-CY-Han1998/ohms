/*
 *  This Source Code Form is subject to the terms of the Mozilla Public
 *  License, v. 2.0. If a copy of the MPL was not distributed with this
 *  file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 *  Copyright (c) 2013, Dennis Sun <dlsun@stanford.edu>
 */

var OHMS = (function(OHMS) {
	
	var Question = function (homework,question) {
	    this.element = question;
	    this.homework = homework;
	    this.id = this.element.attr("id");

	    this.items = [];
	    var item_elements = this.element.find(".item");
	    for(var i=0; i<item_elements.length; i++) {
		var item_element = item_elements.eq(i);
		var type = item_element.attr("type");
		if (type == "multiple-choice") {
		    var item = new OHMS.MultipleChoiceItem(this,item_element);
		} else if (type == "short-answer") {
		    var item = new OHMS.ShortAnswerItem(this,item_element);
		} else if (type == "long-answer") {
		    var item = new OHMS.LongAnswerItem(this,item_element);
		}
		this.items.push(item);
	    }

	    this.load_response();
	    this.bind_events();
	    this.unlock();
	}

	Question.prototype.bind_events = function () {
	    var that = this;
	    // submit onclick handler
	    this.element.find(".submit").click(function () {
		    that.submit_response();
		})
	}

	Question.prototype.load_response = function () {
	    $.ajax({
		    url : "load?q_id=" + this.id,
		    type : "GET",
		    dataType : "json",
		    success : $.proxy(this.load_response_success,this),
		    error : $.proxy(this.load_response_error,this),
		});
	}

	Question.prototype.load_response_success = function (data) {
	    if (data.last_submission.length > 0) {
		for (var i=0; i<this.items.length; i++) {
		    this.items[i].set_value(data.last_submission[i].response);
		}
	    }
	}

	Question.prototype.load_response_error = function (xhr) {
	    console.log(xhr.responseText);
	}

	Question.prototype.submit_response = function () {
	    var that = this;
	    var data = new FormData();
	    for (var i=0; i<this.items.length; i++) {
		data.append("responses",this.items[i].get_value());
	    }
	    var req = new XMLHttpRequest();
	    req.open("POST","submit?q_id=" + this.id,true);
	    req.onload = function (event) {
		if(event.target.status === 200) {
		    data = JSON.parse(event.target.response);
		    $.proxy(that.submit_response_success,that)(data);
		} else {
		    $.proxy(that.submit_response_error,that)(event.target);
		}
	    }
	    req.onerror = this.submit_response_error;
	    req.send(data);
	}

	Question.prototype.submit_response_success = function (data) {
	    console.log(data);
	}

	Question.prototype.submit_response_error = function (xhr) {
	    console.log(xhr.responseText);
	}

	Question.prototype.unlock = function () {
	    for (var i=0; i<this.items.length; i++) {
		this.items[i].unlock();
	    }
	    this.element.find(".submit").removeAttr('disabled');
	}

	OHMS.Question = Question;

	return OHMS;

    }(OHMS));