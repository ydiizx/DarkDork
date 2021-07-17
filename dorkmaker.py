from random import choice

page_formats = ['.php?', '.asp?', '.html?', '.cgi', '.blog?', '.htm']
page_types ='page_id cat category id coID include item_id product_id purchase_id login_id id user_id register game_id type type_id gamer_id user_id username_id page sectionid misc mid feed bookid locale panel GUID membership topicid name CatId genre param pageID cPath words path code storeId option search CartId term countryid refresh show medium file sec return team ReturnUrl sortby auth value login_id ref function referer articleID to pageweb prefix play load loader moviecd coID article activation redirect stream categoryid langcode buy showpage aqs cat topic idx partner source strID mobilesite module blogId site language user_id newsID titleno action users num IdStructure view fileId id serials register encoding color pid utm_source do link plugin format geo ID startTime details PID submit extension list channel r flavour clientId next content_type titleid username_id server filepath read client nextpage subscriptions viewAction mod profile doc model comments keyword include page rangeID title product configFile x imageId redirectTo scid purchase_id issue type query hollywood avd default chapter pagetype lang ad style_id pageindex utmsource q viewpage symbol company documentId content contentId langid owner itemName post sourcedir archive profiles cid url item_id'
search_functions = 'intitle: inurl: intext: allintitle: allinurl: allintext: '
new_sf = "key * site"
default_domain_extensions = 'com, net, org, web, info, gov, edu, co, us, uk, it, fr, de, id, co.us, co.uk, co.it, co.fr, co.de, co.id'
top_level_domain = "arpa root aero biz cat com coop edu gov info int jobs mil mobi museum name net org pro travel ac ad ae af ag ai al am an ao aq ar as at au aw az ba bb bd be bf bg bh bi bj bm bn bo br bs bt bv bw by bz ca cc cd cf cg ch ci ck cl cm cn co cr cu cv cx cy cz de dj dk dm do dz ec ee eg er es et eu fi fj fk fm fo fr ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs gt gu gw gy hk hm hn hr ht hu id ie il im in io iq ir is it je jm jo jp ke kg kh ki km kn kr kw ky kz la lb lc li lk lr ls lt lu lv ly ma mc md me mg mh mk ml mm mn mo mp mq mr ms mt mu mv mW mx my mz na nc ne nF ng ni nl no np nr nu nz om pa pe pF pg ph pk pl pm pn pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr st su sv sy sz tc td tf tg th tj tk tl tm tn to tp tr tt tv tw tz ua ug uk um us uy uz va vc ve vg vi vn vu wf ws ye yt yu za zm zw"
dorktypes = [
        "{KW}{PF}?{PT}= site:{DE}",
        '{SF} "{DE}" + "{KW}"',
        '{SF}{KW}{PF}?{PT}= site:{DE}',
        '{SF}{PT}={KW}{PF}? site:{DE}',
        '{PT}= "{KW}" + "{DE}"',
        '{SF}{KW}{PF}?{PT}= site:{DE}',
        '{SF}{PT}={KW}{PF}? site:{DE}'
        ]

def worker_helper(dork_type):
	parsing = list()
	for i in range(0, len(dork_type)+1):
		temp_dork = dork_type[i-2:i]
		if temp_dork:
			if temp_dork[0].isupper() and temp_dork[1].isupper():
				parsing.append(temp_dork)

	dork_type = "".join(x for x in dork_type if not x.isupper())

	return parsing

def dork_maker(keys_file, file_out, max_dork, method_domain):
	f = open(keys_file, 'r')
	if method_domain == 'manual':
		domains = input("Enter your domain (separate with comma (,)) : ").split(",")
	else:
		f2 = open("Enter manual file or using default: ",)

	data_dict = {
	"DE": domains,
	"PT": page_types.split(),
	"PF": page_formats,
	"SF": search_functions.split(),
	"KW": [x.strip() for x in f.readlines()]
	}

	f.close()

	result = set()

	while len(result) < max_dork:
		dork_type = choice(dorktypes)
		dork_type2 = worker_helper(dork_type)

		for KW in data_dict['KW']:
			for DE in data_dict['DE']:

				temp_dict = dict(KW=KW, DE=DE)
				for x in dork_type2:
					temp_dict[x] = choice(data_dict[x])
				result.add(dork_type.format(**temp_dict))

	f = open(file_out , 'w', encoding='utf-8', errors='surrogateescape')
	for i in result: f.write(i+'\n')
	f.close()
	print("DONE")

if __name__ =='__main__':
	from sys import argv
	if len(argv) < 2:
		print("Usage %s keys.txt file_out.txt 50000 manual")
		exit()
	method_domain= "manual" if argv[4] else ""
	dork_maker(argv[1], argv[2], int(argv[3]), method_domain)