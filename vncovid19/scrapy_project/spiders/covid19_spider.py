import scrapy
import re
from scrapy_project.no_accent_vietnamese import no_accent_vietnamese
    
class Covid19Spider(scrapy.Spider):
    name = "covid19_spider"
    allowed_domains = ["web.archive.org"]
    start_urls = ["https://web.archive.org/web/20210907023426/https://ncov.moh.gov.vn/vi/web/guest/dong-thoi-gian"]
    
    def parse(self, response):
        
        #[I] Load toàn bộ mảng phần nội dung
        timelines = response.xpath("//div[@class='timeline-detail']")
        
        #Regex pattern to extract new_case number
        re_new_case = r'\s([0-9]+)\s'
        
        #Regex pattern to extract city_case number
        re_city_case = r' ([a-zA-Z ]+ \([0-9]+\))'
        
        #[II] Extract data for each timelines
        for timeline in timelines:
            #[1] Extract time value from from timeline head
            time = timeline.xpath(".//div[@class='timeline-head']/h3/text()").get()
            
            #[2] Extract new_case from new_case_content
            new_case_content = timeline.xpath(".//div[@class='timeline-content']/p[2]").get()
            
            #-- Abort new_case_content has no value
            if new_case_content is None:
                continue
            
            #-- Remove dot (.)
            new_case_content = new_case_content.replace(".", "")
            
            #-- Remove accent vietnamese
            new_case_content = no_accent_vietnamese(new_case_content)

            #-- Check and extract new_case_num
            if len(re.findall(re_new_case, new_case_content)) == 0:         
                continue
                
            #-- Get new_case_num
            new_case_num = re.findall(re_new_case, new_case_content)[0]
            
            #[3] Extract city_case from content_city_case
            city_case_content = timeline.xpath(".//div[@class='timeline-content']/p[3]").get()

            city_case_list=[]
            if city_case_content is not None: 
                #Remove accents
                #--Example change "THÔNG BÁO VỀ 13.137 CA MẮC MỚI" -to-> "THONG BAO VE 13.137 CA MAC MOI"
                city_case_content = no_accent_vietnamese(city_case_content)
                
                #Remove dot (.) 
                #--Example change "THONG BAO VE 13.137 CA MAC MOI" -to-> "THONG BAO VE 13137 CA MAC MOI"
                city_case_content = city_case_content.replace(".", "")
                
                #Add none [a-zA-Z ] to using regex for extract the only city in city_case_content 
                #--Example channge "trong nuoc tai TP Ho CHi Minh" -to-> "trong nuoc tai: TP Ho CHi Minh"
                #--Example channge "nhap canh tai Khanh Hoa" -to-> " nhap canh tai: Khanh Hoa"
                #--Example channge "cong dong tai Bac Ninh" -to-> "cong dong tai: Bac Ninh"
                city_case_content = city_case_content.replace("tai", "tai:")
                
                #--Example channge "bo vao tinh Tay Ninh" -to-> "bo vao tinh: Tay Ninh"
                #--Example channge "ngay tai tinh Vinh Long" -to-> "ngay tai tinh: Vinh Long"
                city_case_content = city_case_content.replace("tinh", "tinh:")
                
                #--Example channge "va Kien Giang" -to-> "va: Kien Giang"
                city_case_content = city_case_content.replace("va", "va:")
                
                #Using regex to find array has element format: " city (new_case_num) "
                city_case_arr = re.findall(re_city_case, city_case_content)
        
                for idx in range(len(city_case_arr)):
                    #Change each element format from " city (new_case_num) " to {"city": city, "new_case": new_case_num}
                    city_case_list.append({
                        "city": re.findall("([a-zA-Z ]+) ", city_case_arr[idx])[0],
                        "case": int(re.findall("\(([0-9]+)\)*", city_case_arr[idx])[0])
                    })

            #[4] Extract data to file
            yield {
                'time': time,
                'new_case': new_case_num,
                'case_city': city_case_list
            }
        
        #[III] Go to next_link
        next_link = response.xpath("//div/ul[@class='lfr-pagination-buttons pager']/li[2]/a/@href").get()
        if next_link is not None: 
            yield scrapy.Request(next_link, callback=self.parse)



